"""
Servicios de conteo físico para la app móvil.
Reutiliza RegistroConteoFisico, LoteUbicacion y MovimientoInventario sin cambiar el esquema.
En móvil v1: un solo valor de conteo se replica en primer/segundo/tercer conteo.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional

from django.db import transaction
from django.utils import timezone


ROLES_CONTEO_MOVIL = (
    'Conteo',
    'Almacenero',
    'Administrador',
    'Gestor de Inventario',
    'Supervisión',
)


def usuario_puede_conteo_movil(user) -> bool:
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name__in=ROLES_CONTEO_MOVIL).exists()


@dataclass
class ResultadoConteo:
    lote_ubicacion_id: int
    movimiento_id: Optional[int]
    cantidad_anterior: int
    cantidad_nueva: int
    diferencia: int
    tipo_movimiento: str
    completado: bool
    progreso: str


def _tipo_movimiento_por_diferencia(diferencia: int) -> str:
    """Misma lógica que conteo por ubicación en views_conteo_fisico_v2."""
    if diferencia > 0:
        return 'AJUSTE_POSITIVO'
    if diferencia < 0:
        return 'AJUSTE_NEGATIVO'
    return 'AJUSTE_POSITIVO'


def _motivo_conteo(registro, cantidad_fisica: int, diferencia: int, observaciones: str, origen: str) -> str:
    lineas = [
        f'Conteo Físico IMSS-Bienestar ({origen}):',
        f'- Primer Conteo: {registro.primer_conteo}',
        f'- Segundo Conteo: {registro.segundo_conteo}',
        f'- Tercer Conteo (Definitivo): {registro.tercer_conteo}',
        f'- Diferencia: {diferencia:+d}',
    ]
    if observaciones:
        lineas.append(f'- Observaciones: {observaciones}')
    return '\n'.join(lineas)


@transaction.atomic
def registrar_conteo_ubicacion(
    lote_ubicacion_id: int,
    usuario,
    cantidad_fisica: int,
    *,
    fecha_caducidad: Optional[date] = None,
    observaciones: str = '',
    origen: str = 'App móvil',
) -> ResultadoConteo:
    """
    Registra conteo en una LoteUbicacion.
    cantidad_fisica se guarda en los 3 conteos y aplica existencia de inmediato.
    """
    from inventario.models import LoteUbicacion, MovimientoInventario, RegistroConteoFisico

    if cantidad_fisica < 0:
        raise ValueError('La cantidad física no puede ser negativa.')

    lote_ubicacion = (
        LoteUbicacion.objects.select_related('lote', 'lote__producto', 'ubicacion', 'ubicacion__almacen')
        .get(pk=lote_ubicacion_id)
    )
    lote = lote_ubicacion.lote

    registro, _ = RegistroConteoFisico.objects.get_or_create(
        lote_ubicacion=lote_ubicacion,
        defaults={'usuario_creacion': usuario},
    )

    cantidad_anterior = lote_ubicacion.cantidad
    cantidad_nueva = int(cantidad_fisica)
    diferencia = cantidad_nueva - cantidad_anterior

    registro.primer_conteo = cantidad_nueva
    registro.segundo_conteo = cantidad_nueva
    registro.tercer_conteo = cantidad_nueva
    if observaciones:
        registro.observaciones = observaciones
    registro.usuario_ultima_actualizacion = usuario
    registro.completado = True
    registro.save()

    lote_ubicacion.cantidad = cantidad_nueva
    lote_ubicacion.usuario_asignacion = usuario
    lote_ubicacion.save(update_fields=['cantidad', 'usuario_asignacion', 'fecha_actualizacion'])

    movimiento_caducidad_id = None
    if fecha_caducidad and lote.fecha_caducidad != fecha_caducidad:
        movimiento_caducidad_id = _ajustar_caducidad_lote(
            lote, fecha_caducidad, usuario, origen=origen
        )

    lote.sincronizar_cantidad_disponible()

    tipo_mov = _tipo_movimiento_por_diferencia(diferencia)
    motivo = _motivo_conteo(registro, cantidad_nueva, diferencia, observaciones, origen)

    movimiento = MovimientoInventario.objects.create(
        lote=lote,
        tipo_movimiento=tipo_mov,
        cantidad=abs(diferencia),
        cantidad_anterior=cantidad_anterior,
        cantidad_nueva=cantidad_nueva,
        motivo=motivo,
        usuario=usuario,
        folio=f'CONTEO-{timezone.now().strftime("%Y%m%d%H%M%S")}',
    )

    return ResultadoConteo(
        lote_ubicacion_id=lote_ubicacion.id,
        movimiento_id=movimiento.id,
        cantidad_anterior=cantidad_anterior,
        cantidad_nueva=cantidad_nueva,
        diferencia=diferencia,
        tipo_movimiento=tipo_mov,
        completado=True,
        progreso=registro.progreso,
    )


def _ajustar_caducidad_lote(lote, fecha_caducidad: date, usuario, origen: str = 'App móvil') -> int:
    from inventario.models import MovimientoInventario

    anterior = lote.fecha_caducidad
    lote.fecha_caducidad = fecha_caducidad
    lote.save(update_fields=['fecha_caducidad'])

    cantidad = lote.cantidad_disponible or 0
    mov = MovimientoInventario.objects.create(
        lote=lote,
        tipo_movimiento='AJUSTE_DATOS_LOTE',
        cantidad=max(cantidad, 1),
        cantidad_anterior=cantidad,
        cantidad_nueva=cantidad,
        motivo=(
            f'Ajuste caducidad ({origen}): '
            f'{anterior.strftime("%d/%m/%Y") if anterior else "—"} → '
            f'{fecha_caducidad.strftime("%d/%m/%Y")}'
        ),
        usuario=usuario,
        folio=f'CONTEO-CAD-{timezone.now().strftime("%Y%m%d%H%M%S")}',
    )
    return mov.id


@transaction.atomic
def crear_lote_en_ubicacion(
    ubicacion_id: int,
    usuario,
    clave_cnis: str,
    numero_lote: str,
    cantidad_inicial: int,
    fecha_caducidad: date,
    *,
    precio_unitario=None,
    observaciones: str = '',
) -> dict:
    """
    Alta de lote en ubicación (mismo esquema Lote + LoteUbicacion) y conteo inicial.
    """
    from decimal import Decimal

    from inventario.models import (
        Lote,
        LoteUbicacion,
        Producto,
        UbicacionAlmacen,
    )

    if cantidad_inicial < 0:
        raise ValueError('La cantidad inicial no puede ser negativa.')

    ubicacion = UbicacionAlmacen.objects.select_related('almacen', 'almacen__institucion').get(pk=ubicacion_id)
    almacen = ubicacion.almacen
    institucion = almacen.institucion

    producto = Producto.objects.filter(clave_cnis=clave_cnis.strip()).first()
    if not producto:
        raise ValueError(f'Clave {clave_cnis} no existe en catálogo. Dé de alta el producto en sistema web.')

    precio = Decimal(str(precio_unitario)) if precio_unitario is not None else Decimal('0.01')
    if precio <= 0:
        precio = Decimal('0.01')
    cantidad = max(int(cantidad_inicial), 0)
    valor_total = precio * Decimal(cantidad) if cantidad else Decimal('0.01')

    lote_existente = Lote.objects.filter(
        numero_lote=numero_lote.strip(),
        producto=producto,
        institucion=institucion,
    ).first()

    if lote_existente:
        lote_ubi, created = LoteUbicacion.objects.get_or_create(
            lote=lote_existente,
            ubicacion=ubicacion,
            defaults={'cantidad': cantidad, 'usuario_asignacion': usuario},
        )
        if not created:
            raise ValueError(
                'Ya existe ese lote en esta ubicación. Use conteo para ajustar cantidad.'
            )
        lote = lote_existente
    else:
        hoy = timezone.now().date()
        lote = Lote.objects.create(
            producto=producto,
            numero_lote=numero_lote.strip(),
            institucion=institucion,
            almacen=almacen,
            ubicacion=ubicacion,
            cantidad_inicial=max(cantidad, 1) if cantidad == 0 else cantidad,
            cantidad_disponible=max(cantidad, 1) if cantidad == 0 else cantidad,
            cantidad_reservada=0,
            precio_unitario=precio,
            valor_total=valor_total if valor_total >= Decimal('0.01') else Decimal('0.01'),
            fecha_caducidad=fecha_caducidad,
            fecha_recepcion=hoy,
            estado=1,
        )
        lote_ubi = LoteUbicacion.objects.create(
            lote=lote,
            ubicacion=ubicacion,
            cantidad=cantidad,
            usuario_asignacion=usuario,
        )

    lote.sincronizar_cantidad_disponible()

    resultado = registrar_conteo_ubicacion(
        lote_ubi.id,
        usuario,
        cantidad,
        fecha_caducidad=fecha_caducidad,
        observaciones=observaciones or 'Alta de lote desde app móvil',
        origen='App móvil — alta lote',
    )

    return {
        'lote_id': lote.id,
        'lote_ubicacion_id': lote_ubi.id,
        'conteo': resultado,
    }


def listar_lotes_ubicacion(ubicacion_id: int) -> list[dict]:
    from inventario.models import LoteUbicacion, RegistroConteoFisico

    qs = (
        LoteUbicacion.objects.filter(ubicacion_id=ubicacion_id)
        .select_related('lote', 'lote__producto', 'ubicacion')
        .order_by('lote__producto__clave_cnis', 'lote__numero_lote')
    )
    registros = {
        r.lote_ubicacion_id: r
        for r in RegistroConteoFisico.objects.filter(lote_ubicacion__ubicacion_id=ubicacion_id)
    }

    filas = []
    for lu in qs:
        registro = registros.get(lu.id)
        filas.append(
            {
                'lote_ubicacion_id': lu.id,
                'clave_cnis': lu.lote.producto.clave_cnis,
                'descripcion': (lu.lote.producto.descripcion or '')[:120],
                'numero_lote': lu.lote.numero_lote,
                'fecha_caducidad': lu.lote.fecha_caducidad.isoformat() if lu.lote.fecha_caducidad else None,
                'cantidad_sistema': lu.cantidad,
                'conteo_completado': bool(registro and registro.completado),
                'progreso_conteo': registro.progreso if registro else '0/3',
                'ultimo_tercer_conteo': registro.tercer_conteo if registro else None,
            }
        )
    return filas
