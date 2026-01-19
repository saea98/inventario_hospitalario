"""
Utilidades para el módulo de Gestión de Pedidos
Incluye funciones para logging de errores y envío de alertas
"""

import logging
import requests
from django.conf import settings
from django.utils import timezone
from .pedidos_models import LogErrorPedido
from .models import Institucion, Almacen

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
