"""
Servicios de inventario para entradas por transferencia.
Reutiliza la ubicación staging de llegadas de proveedor.
"""

from datetime import date

from django.db import transaction
from django.utils import timezone

from .llegada_views import get_staging_almacen_ubicacion


def resolver_producto_transferencia(clave, descripcion=''):
    """
    Busca producto por clave; si no existe, crea uno mínimo para permitir captura
    de claves aún no catalogadas.
    """
    from .models import CategoriaProducto, Producto

    clave = (clave or '').strip()
    if not clave:
        raise ValueError('La clave CNIS es obligatoria.')

    producto = Producto.objects.filter(clave_cnis=clave).first()
    if producto:
        return producto

    categoria, _ = CategoriaProducto.objects.get_or_create(
        nombre='Transferencias (sin catalogar)',
        defaults={'activa': True},
    )
    desc = (descripcion or '').strip() or f'Producto transferencia {clave}'
    return Producto.objects.create(
        clave_cnis=clave,
        descripcion=desc,
        categoria=categoria,
        unidad_medida='PIEZA',
        activo=True,
        precio_unitario_referencia=None,
    )


def asignar_transferencia_a_staging(transferencia, usuario):
    """
    Asigna ítems a staging (misma lógica que llegada de proveedor).
    Crea/actualiza Lote, LoteUbicacion y MovimientoInventario tipo ENTRADA.
    """
    from .models import Lote, LoteUbicacion, MovimientoInventario

    almacen_staging, ubicacion_staging = get_staging_almacen_ubicacion()
    if not almacen_staging or not ubicacion_staging:
        return False, (
            "No se encontró el almacén con código XXXX010101 o la ubicación 'staging'. "
            'Configurelos en el sistema.'
        )

    institucion = almacen_staging.institucion
    mensajes_lote_existente = []
    fecha_caducidad_default = date(2099, 12, 31)

    with transaction.atomic():
        for item in transferencia.items.select_related('producto'):
            cantidad_recibida = item.cantidad_recibida
            fecha_cad = item.fecha_caducidad or fecha_caducidad_default
            producto_desc = item.descripcion_mostrar or item.clave
            precio_unit = item.precio_unitario_sin_iva or 0
            incremento_valor = precio_unit * cantidad_recibida

            lote_existente = Lote.objects.filter(
                numero_lote=item.numero_lote,
                producto=item.producto,
                institucion=institucion,
            ).first()

            if lote_existente:
                lote = lote_existente
                cantidad_anterior_lote = lote.cantidad_disponible
                lote.cantidad_inicial += cantidad_recibida
                lote.cantidad_disponible += cantidad_recibida
                lote.valor_total += incremento_valor
                lote.almacen = almacen_staging
                lote.save()
                lote_ubi, created = LoteUbicacion.objects.get_or_create(
                    lote=lote,
                    ubicacion=ubicacion_staging,
                    defaults={'cantidad': cantidad_recibida, 'usuario_asignacion': usuario},
                )
                if not created:
                    lote_ubi.cantidad += cantidad_recibida
                    lote_ubi.save(update_fields=['cantidad'])
                MovimientoInventario.objects.create(
                    lote=lote,
                    tipo_movimiento='ENTRADA',
                    cantidad=cantidad_recibida,
                    cantidad_anterior=cantidad_anterior_lote,
                    cantidad_nueva=lote.cantidad_disponible,
                    motivo=(
                        f'Entrada por transferencia - Folio: {transferencia.folio} '
                        f'(asignación automática a staging)'
                    ),
                    documento_referencia=transferencia.remision,
                    remision=transferencia.remision,
                    folio=transferencia.folio,
                    usuario=usuario,
                )
                desc = (producto_desc or '')[:40]
                if len(producto_desc or '') > 40:
                    desc += '…'
                mensajes_lote_existente.append(
                    f'Lote {lote.numero_lote} ({desc}): se sumaron {cantidad_recibida} unidades.'
                )
            elif item.lote_creado_id:
                lote = item.lote_creado
                lote.almacen = almacen_staging
                lote.save()
                lote.ubicaciones_detalle.all().delete()
                LoteUbicacion.objects.create(
                    lote=lote,
                    ubicacion=ubicacion_staging,
                    cantidad=cantidad_recibida,
                    usuario_asignacion=usuario,
                )
                MovimientoInventario.objects.create(
                    lote=lote,
                    tipo_movimiento='ENTRADA',
                    cantidad=cantidad_recibida,
                    cantidad_anterior=0,
                    cantidad_nueva=cantidad_recibida,
                    motivo=(
                        f'Entrada por transferencia - Folio: {transferencia.folio} '
                        f'(asignación automática a staging)'
                    ),
                    documento_referencia=transferencia.remision,
                    remision=transferencia.remision,
                    folio=transferencia.folio,
                    usuario=usuario,
                )
            else:
                lote = Lote.objects.create(
                    producto=item.producto,
                    numero_lote=item.numero_lote,
                    fecha_caducidad=fecha_cad,
                    cantidad_inicial=cantidad_recibida,
                    cantidad_disponible=cantidad_recibida,
                    cantidad_reservada=0,
                    almacen=almacen_staging,
                    institucion=institucion,
                    precio_unitario=precio_unit,
                    valor_total=incremento_valor,
                    fecha_recepcion=transferencia.fecha_recepcion.date()
                    if transferencia.fecha_recepcion
                    else date.today(),
                    estado=1,
                )
                item.lote_creado = lote
                item.save(update_fields=['lote_creado'])
                try:
                    from .lote_utils import completar_datos_lote_desde_transferencia

                    completar_datos_lote_desde_transferencia(lote, item)
                except Exception:
                    pass
                LoteUbicacion.objects.create(
                    lote=lote,
                    ubicacion=ubicacion_staging,
                    cantidad=cantidad_recibida,
                    usuario_asignacion=usuario,
                )
                MovimientoInventario.objects.create(
                    lote=lote,
                    tipo_movimiento='ENTRADA',
                    cantidad=cantidad_recibida,
                    cantidad_anterior=0,
                    cantidad_nueva=cantidad_recibida,
                    motivo=(
                        f'Entrada por transferencia - Folio: {transferencia.folio} '
                        f'(asignación automática a staging)'
                    ),
                    documento_referencia=transferencia.remision,
                    remision=transferencia.remision,
                    folio=transferencia.folio,
                    usuario=usuario,
                )

        transferencia.estado = 'APROBADA'
        transferencia.usuario_aprobacion = usuario
        transferencia.fecha_aprobacion = timezone.now()
        transferencia.save(
            update_fields=['estado', 'usuario_aprobacion', 'fecha_aprobacion', 'fecha_actualizacion']
        )

    return True, mensajes_lote_existente
