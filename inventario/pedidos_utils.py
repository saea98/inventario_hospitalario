"""
Utilidades para el módulo de Gestión de Pedidos
Incluye funciones para logging de errores y envío de alertas
"""

import csv
import io
import logging
import requests
from django.conf import settings
from django.utils import timezone
from .pedidos_models import LogErrorPedido, Producto, ItemSolicitud
from .models import Institucion, Almacen

# Máximo de advertencias en pantalla tras CSV (evita render pesado)
MAX_ADVERTENCIAS_CSV_UI = 15

# Carga CSV en crear pedido: ítems en sesión (evita formset gigante + Select2 por renglón)
SESSION_CREAR_PEDIDO_CSV_ITEMS = 'crear_pedido_csv_items'
SESSION_CREAR_PEDIDO_HEADER = 'crear_pedido_csv_header'
CSV_PREVIEW_MAX_FILAS = 50
CSV_ITEMS_MAX = 10000

logger = logging.getLogger(__name__)


def registrar_error_pedido(
    usuario,
    tipo_error,
    clave_solicitada,
    cantidad_solicitada=None,
    descripcion_error="",
    institucion=None,
    almacen=None,
    enviar_alerta=True
):
    """
    Registra un error durante la carga masiva de pedidos.
    
    Args:
        usuario: Usuario que realizó la carga
        tipo_error: Tipo de error (CLAVE_NO_EXISTE, SIN_EXISTENCIA, etc.)
        clave_solicitada: Clave del producto solicitado
        cantidad_solicitada: Cantidad solicitada (opcional)
        descripcion_error: Descripción detallada del error
        institucion: Institución solicitante (opcional)
        almacen: Almacén destino (opcional)
        enviar_alerta: Si se debe enviar alerta por Telegram
    
    Returns:
        LogErrorPedido: Objeto del log creado
    """
    try:
        log_error = LogErrorPedido.objects.create(
            usuario=usuario,
            tipo_error=tipo_error,
            clave_solicitada=clave_solicitada,
            cantidad_solicitada=cantidad_solicitada,
            descripcion_error=descripcion_error,
            institucion=institucion,
            almacen=almacen,
            alerta_enviada=False
        )
        
        logger.info(
            f"Error registrado: {tipo_error} - Clave: {clave_solicitada} - "
            f"Usuario: {usuario.username}"
        )
        
        # Enviar alerta por Telegram si está habilitado
        if enviar_alerta:
            enviar_alerta_telegram(log_error)
        
        return log_error
    
    except Exception as e:
        logger.error(f"Error al registrar error de pedido: {str(e)}", exc_info=True)
        return None


def enviar_alerta_telegram(log_error):
    """
    Envía una alerta por Telegram cuando ocurre un error en la carga masiva.
    
    Args:
        log_error: Objeto LogErrorPedido con la información del error
    """
    try:
        # Verificar que Telegram esté configurado
        telegram_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
        telegram_chat_id = getattr(settings, 'TELEGRAM_CHAT_ID_PEDIDOS', None)
        
        if not telegram_token or not telegram_chat_id:
            logger.warning("Telegram no está configurado para alertas de pedidos")
            return False
        
        # Construir mensaje
        mensaje = construir_mensaje_alerta(log_error)
        
        # Enviar por Telegram
        url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
        payload = {
            "chat_id": telegram_chat_id,
            "text": mensaje,
            "parse_mode": "HTML"
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            # Marcar como alerta enviada
            log_error.alerta_enviada = True
            log_error.fecha_alerta = timezone.now()
            log_error.save()
            
            logger.info(f"Alerta enviada por Telegram para error: {log_error.id}")
            return True
        else:
            logger.error(
                f"Error al enviar alerta por Telegram: {response.status_code} - "
                f"{response.text}"
            )
            return False
    
    except Exception as e:
        logger.error(f"Error al enviar alerta por Telegram: {str(e)}", exc_info=True)
        return False


def construir_mensaje_alerta(log_error):
    """
    Construye el mensaje de alerta para Telegram.
    
    Args:
        log_error: Objeto LogErrorPedido
    
    Returns:
        str: Mensaje formateado para Telegram
    """
    tipo_error = log_error.get_tipo_error_display()
    fecha = log_error.fecha_error.strftime("%d/%m/%Y %H:%M")
    usuario = log_error.usuario.get_full_name() if log_error.usuario else "Desconocido"
    
    mensaje = f"""
<b>⚠️ ERROR EN CARGA MASIVA DE PEDIDOS</b>

<b>Tipo de Error:</b> {tipo_error}
<b>Clave:</b> {log_error.clave_solicitada}
<b>Cantidad:</b> {log_error.cantidad_solicitada or 'N/A'} unidades
<b>Usuario:</b> {usuario}
<b>Fecha:</b> {fecha}

<b>Descripción:</b>
{log_error.descripcion_error}

<b>Institución:</b> {log_error.institucion.nombre if log_error.institucion else 'N/A'}
<b>Almacén:</b> {log_error.almacen.nombre if log_error.almacen else 'N/A'}
"""
    
    return mensaje.strip()


def decodificar_csv_pedidos(contenido_bytes):
    """Decodifica bytes de CSV probando codificaciones habituales en México."""
    codificaciones = ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
    for codificacion in codificaciones:
        try:
            return contenido_bytes.decode(codificacion)
        except (UnicodeDecodeError, AttributeError):
            continue
    raise ValueError('No se pudo decodificar el archivo con ninguna codificación soportada')


def _normalizar_clave_header_csv(k):
    if k is None:
        return ''
    return str(k).replace('\ufeff', '').strip().upper()


def _extraer_folio_desde_filas_csv(rows):
    for row in rows:
        for k, v in row.items():
            if _normalizar_clave_header_csv(k) == 'FOLIO' and v is not None:
                s = str(v).strip()
                if s:
                    return s
    return ''


def procesar_csv_crear_solicitud_pedido(
    contenido_bytes,
    usuario,
    institucion=None,
    almacen=None,
):
    """
    Procesa CSV de crear pedido con una sola consulta de catálogo (por lotes).

    Antes: Producto.objects.get() por fila + Telegram por error → CPU/red altos.
    Ahora: acumula cantidades, carga productos con __in__, errores en bulk_create sin Telegram.

    Returns:
        dict con items_data, folio_desde_csv, conteos y listas para mensajes UI.
    """
    decoded = decodificar_csv_pedidos(contenido_bytes)
    rows = list(csv.DictReader(io.StringIO(decoded)))
    folio_desde_csv = _extraer_folio_desde_filas_csv(rows)

    cantidad_por_clave = {}
    errores_cantidad = []

    for row in rows:
        clave = (row.get('CLAVE') or '').strip()
        cantidad = row.get('CANTIDAD SOLICITADA')
        if not clave or cantidad is None or str(cantidad).strip() == '':
            continue
        try:
            cantidad_int = int(cantidad)
        except (TypeError, ValueError):
            errores_cantidad.append((clave, str(cantidad)))
            continue
        if cantidad_int < 0:
            errores_cantidad.append((clave, str(cantidad)))
            continue
        cantidad_por_clave[clave] = cantidad_por_clave.get(clave, 0) + cantidad_int

    claves = list(cantidad_por_clave.keys())
    productos_map = {}
    chunk = 500
    for i in range(0, len(claves), chunk):
        lote = claves[i : i + chunk]
        for p in Producto.objects.filter(clave_cnis__in=lote).only('id', 'clave_cnis'):
            productos_map[p.clave_cnis] = p

    items_data = []
    logs_bulk = []
    claves_no_existen = []

    for clave, cantidad_total in cantidad_por_clave.items():
        producto = productos_map.get(clave)
        if not producto:
            claves_no_existen.append(clave)
            logs_bulk.append(
                LogErrorPedido(
                    usuario=usuario,
                    tipo_error='CLAVE_NO_EXISTE',
                    clave_solicitada=clave[:50],
                    cantidad_solicitada=cantidad_total,
                    descripcion_error='Clave no existe en catálogo',
                    institucion=institucion,
                    almacen=almacen,
                )
            )
            continue
        items_data.append(
            {
                'producto': producto.id,
                'cantidad_solicitada': cantidad_total,
                'cantidad_aprobada': None,
            }
        )

    for clave, cant_raw in errores_cantidad:
        logs_bulk.append(
            LogErrorPedido(
                usuario=usuario,
                tipo_error='CANTIDAD_INVALIDA',
                clave_solicitada=(clave or '?')[:50],
                cantidad_solicitada=None,
                descripcion_error=f'Cantidad no válida: {cant_raw}',
                institucion=institucion,
                almacen=almacen,
            )
        )

    if logs_bulk:
        LogErrorPedido.objects.bulk_create(logs_bulk, batch_size=500)
        logger.info(
            'CSV pedido: %s errores registrados (bulk, sin Telegram por fila)',
            len(logs_bulk),
        )

    return {
        'items_data': items_data,
        'folio_desde_csv': folio_desde_csv,
        'total_filas_csv': len(rows),
        'claves_ok': len(items_data),
        'claves_no_existen': claves_no_existen,
        'errores_cantidad': errores_cantidad,
        'total_errores': len(logs_bulk),
    }


def mensajes_advertencia_csv(resultado):
    """Genera textos breves para messages.warning (limitados)."""
    textos = []

    for clave in resultado['claves_no_existen']:
        textos.append(f'Clave {clave} no existe en el catálogo.')

    for clave, cant in resultado['errores_cantidad']:
        textos.append(f'Cantidad inválida para clave {clave}: {cant}')

    if len(textos) > MAX_ADVERTENCIAS_CSV_UI:
        omitidos = len(textos) - MAX_ADVERTENCIAS_CSV_UI
        textos = textos[:MAX_ADVERTENCIAS_CSV_UI]
        textos.append(
            f'… y {omitidos} advertencia(s) más (consulte el reporte de errores de pedidos).'
        )

    return textos


def _cantidad_aprobada_desde_item_data(cantidad_solicitada, cantidad_aprobada):
    if cantidad_aprobada is None or cantidad_aprobada == '':
        return cantidad_solicitada
    return int(cantidad_aprobada)


def serializar_header_crear_pedido(cleaned_data):
    """Guarda en sesión los campos del encabezado del pedido (IDs y fechas serializables)."""
    fecha = cleaned_data.get('fecha_entrega_programada')
    return {
        'institucion_solicitante': cleaned_data['institucion_solicitante'].pk,
        'almacen_destino': cleaned_data['almacen_destino'].pk,
        'fecha_entrega_programada': fecha.isoformat() if fecha else None,
        'observaciones_solicitud': (cleaned_data.get('observaciones_solicitud') or '').strip(),
    }


def guardar_csv_en_sesion_crear_pedido(request, items_data, header_serializado):
    request.session[SESSION_CREAR_PEDIDO_CSV_ITEMS] = items_data
    request.session[SESSION_CREAR_PEDIDO_HEADER] = header_serializado
    request.session.modified = True


def limpiar_csv_sesion_crear_pedido(request):
    request.session.pop(SESSION_CREAR_PEDIDO_CSV_ITEMS, None)
    request.session.pop(SESSION_CREAR_PEDIDO_HEADER, None)
    request.session.modified = True


def obtener_items_csv_sesion_crear_pedido(request):
    return request.session.get(SESSION_CREAR_PEDIDO_CSV_ITEMS) or []


def obtener_header_csv_sesion_crear_pedido(request):
    return request.session.get(SESSION_CREAR_PEDIDO_HEADER)


def preparar_filas_vista_previa_csv(items_data, max_filas=CSV_PREVIEW_MAX_FILAS):
    """Filas ligeras para plantilla (sin formset por renglón)."""
    if not items_data:
        return [], 0
    ids = {row['producto'] for row in items_data}
    productos = {
        p.id: p
        for p in Producto.objects.filter(id__in=ids).only('id', 'clave_cnis', 'descripcion')
    }
    filas = []
    for row in items_data[:max_filas]:
        producto = productos.get(row['producto'])
        filas.append({
            'clave_cnis': producto.clave_cnis if producto else '—',
            'descripcion': (producto.descripcion[:80] if producto and producto.descripcion else '—'),
            'cantidad_solicitada': row['cantidad_solicitada'],
        })
    return filas, len(items_data)


def bulk_crear_items_solicitud_pedido(solicitud, items_data):
    """Crea ítems en bloque (misma lógica de cantidad aprobada que el formulario)."""
    objetos = []
    for row in items_data:
        cant_sol = row['cantidad_solicitada']
        cant_apr = _cantidad_aprobada_desde_item_data(cant_sol, row.get('cantidad_aprobada'))
        objetos.append(
            ItemSolicitud(
                solicitud=solicitud,
                producto_id=row['producto'],
                cantidad_solicitada=cant_sol,
                cantidad_aprobada=cant_apr,
                justificacion_cambio=row.get('justificacion_cambio') or '',
            )
        )
    if objetos:
        ItemSolicitud.objects.bulk_create(objetos, batch_size=500)
    return len(objetos)


def obtener_resumen_errores(fecha_inicio=None, fecha_fin=None, tipo_error=None):
    """
    Obtiene un resumen de los errores registrados en un período.
    
    Args:
        fecha_inicio: Fecha de inicio (opcional)
        fecha_fin: Fecha de fin (opcional)
        tipo_error: Tipo de error a filtrar (opcional)
    
    Returns:
        dict: Resumen con estadísticas de errores
    """
    queryset = LogErrorPedido.objects.all()
    
    if fecha_inicio:
        queryset = queryset.filter(fecha_error__gte=fecha_inicio)
    if fecha_fin:
        queryset = queryset.filter(fecha_error__lte=fecha_fin)
    if tipo_error:
        queryset = queryset.filter(tipo_error=tipo_error)
    
    # Contar errores por tipo
    errores_por_tipo = {}
    for tipo, _ in LogErrorPedido.TIPO_ERROR_CHOICES:
        count = queryset.filter(tipo_error=tipo).count()
        if count > 0:
            errores_por_tipo[tipo] = count
    
    # Contar errores por institución
    errores_por_institucion = {}
    for institucion in Institucion.objects.all():
        count = queryset.filter(institucion=institucion).count()
        if count > 0:
            errores_por_institucion[institucion.nombre] = count
    
    # Contar errores por usuario
    errores_por_usuario = {}
    for log in queryset.values('usuario__username').distinct():
        username = log['usuario__username']
        count = queryset.filter(usuario__username=username).count()
        if count > 0:
            errores_por_usuario[username] = count
    
    return {
        'total_errores': queryset.count(),
        'errores_por_tipo': errores_por_tipo,
        'errores_por_institucion': errores_por_institucion,
        'errores_por_usuario': errores_por_usuario,
        'claves_sin_existencia': queryset.filter(
            tipo_error='SIN_EXISTENCIA'
        ).values_list('clave_solicitada', flat=True).distinct(),
        'claves_no_existen': queryset.filter(
            tipo_error='CLAVE_NO_EXISTE'
        ).values_list('clave_solicitada', flat=True).distinct(),
    }
