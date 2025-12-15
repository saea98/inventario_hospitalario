"""
Servicio de Notificaciones para Email y Telegram

Proporciona funcionalidades para:
- Enviar notificaciones por Email
- Enviar notificaciones por Telegram
- Registrar logs de notificaciones
- Gestionar configuración centralizada
"""

import requests
import logging
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from django.conf import settings
from .models import ConfiguracionNotificaciones, LogNotificaciones

logger = logging.getLogger(__name__)


class ServicioNotificaciones:
    """Servicio centralizado para gestionar notificaciones"""
    
    def __init__(self):
        """Inicializar el servicio y obtener configuración"""
        try:
            self.config = ConfiguracionNotificaciones.objects.first()
        except:
            self.config = None
    
    def obtener_configuracion(self):
        """Obtener configuración actual"""
        if not self.config:
            self.config = ConfiguracionNotificaciones.objects.first()
        return self.config
    
    # ========================================================================
    # NOTIFICACIONES POR EMAIL
    # ========================================================================
    
    def enviar_email(self, asunto, mensaje, destinatarios=None, evento='email_generico', usuario=None):
        """
        Enviar notificación por Email
        
        Args:
            asunto: Asunto del email
            mensaje: Cuerpo del email (puede ser HTML)
            destinatarios: Lista de emails o None (usa configuración)
            evento: Tipo de evento para logging
            usuario: Usuario relacionado (opcional)
        
        Returns:
            dict: {'exitoso': bool, 'mensaje': str, 'log_id': int}
        """
        config = self.obtener_configuracion()
        
        if not config or not config.email_habilitado:
            return {
                'exitoso': False,
                'mensaje': 'Email no habilitado en configuración',
                'log_id': None
            }
        
        # Obtener destinatarios
        if not destinatarios:
            destinatarios = config.obtener_emails_destinatarios()
        
        if not destinatarios:
            return {
                'exitoso': False,
                'mensaje': 'No hay destinatarios configurados',
                'log_id': None
            }
        
        # Crear log de notificación
        log = LogNotificaciones.objects.create(
            tipo='email',
            evento=evento,
            asunto=asunto,
            mensaje=mensaje,
            destinatarios=', '.join(destinatarios),
            estado='pendiente',
            usuario_relacionado=usuario
        )
        
        try:
            # Enviar email
            send_mail(
                subject=asunto,
                message=mensaje,
                from_email=config.email_remitente,
                recipient_list=destinatarios,
                fail_silently=False,
                html_message=mensaje  # Permitir HTML
            )
            
            # Actualizar log
            log.estado = 'enviada'
            log.fecha_entrega = timezone.now()
            log.respuesta = 'Email enviado exitosamente'
            log.save()
            
            logger.info(f"Email enviado: {asunto} a {', '.join(destinatarios)}")
            
            return {
                'exitoso': True,
                'mensaje': 'Email enviado exitosamente',
                'log_id': log.id
            }
        
        except Exception as e:
            # Registrar error
            log.estado = 'error'
            log.respuesta = str(e)
            log.save()
            
            logger.error(f"Error al enviar email: {str(e)}")
            
            return {
                'exitoso': False,
                'mensaje': f'Error al enviar email: {str(e)}',
                'log_id': log.id
            }
    
    # ========================================================================
    # NOTIFICACIONES POR TELEGRAM
    # ========================================================================
    
    def enviar_telegram(self, mensaje, evento='telegram_generico', usuario=None):
        """
        Enviar notificación por Telegram
        
        Args:
            mensaje: Mensaje a enviar (Markdown)
            evento: Tipo de evento para logging
            usuario: Usuario relacionado (opcional)
        
        Returns:
            dict: {'exitoso': bool, 'mensaje': str, 'log_id': int}
        """
        config = self.obtener_configuracion()
        
        if not config or not config.telegram_habilitado:
            return {
                'exitoso': False,
                'mensaje': 'Telegram no habilitado en configuración',
                'log_id': None
            }
        
        # Validar configuración
        valido, msg = config.validar_configuracion_telegram()
        if not valido:
            return {
                'exitoso': False,
                'mensaje': msg,
                'log_id': None
            }
        
        # Crear log de notificación
        log = LogNotificaciones.objects.create(
            tipo='telegram',
            evento=evento,
            asunto=f'Notificación Telegram: {evento}',
            mensaje=mensaje,
            destinatarios=config.telegram_chat_id,
            estado='pendiente',
            usuario_relacionado=usuario
        )
        
        try:
            # Construir URL de Telegram
            url = f"https://api.telegram.org/bot{config.telegram_token}/sendMessage"
            
            # Preparar datos
            datos = {
                'chat_id': config.telegram_chat_id,
                'text': mensaje,
                'parse_mode': 'Markdown'  # Usar Markdown en lugar de HTML
            }
            
            # Enviar mensaje
            respuesta = requests.post(url, json=datos, timeout=10)
            
            if respuesta.status_code == 200:
                # Actualizar log
                log.estado = 'enviada'
                log.fecha_entrega = timezone.now()
                log.respuesta = 'Mensaje enviado a Telegram exitosamente'
                log.save()
                
                logger.info(f"Mensaje Telegram enviado: {evento}")
                
                return {
                    'exitoso': True,
                    'mensaje': 'Mensaje enviado a Telegram exitosamente',
                    'log_id': log.id
                }
            else:
                # Error en respuesta
                log.estado = 'error'
                log.respuesta = f"Error {respuesta.status_code}: {respuesta.text}"
                log.save()
                
                logger.error(f"Error Telegram {respuesta.status_code}: {respuesta.text}")
                
                return {
                    'exitoso': False,
                    'mensaje': f'Error al enviar a Telegram: {respuesta.text}',
                    'log_id': log.id
                }
        
        except Exception as e:
            # Registrar error
            log.estado = 'error'
            log.respuesta = str(e)
            log.save()
            
            logger.error(f"Error al enviar Telegram: {str(e)}")
            
            return {
                'exitoso': False,
                'mensaje': f'Error al enviar a Telegram: {str(e)}',
                'log_id': log.id
            }
    
    # ========================================================================
    # NOTIFICACIONES COMBINADAS
    # ========================================================================
    
    def enviar_notificacion(self, asunto, mensaje, evento, usuario=None, destinatarios=None):
        """
        Enviar notificación por Email y/o Telegram según configuración
        
        Args:
            asunto: Asunto del email
            mensaje: Cuerpo del mensaje
            evento: Tipo de evento
            usuario: Usuario relacionado
            destinatarios: Lista de emails (opcional)
        
        Returns:
            dict: Resultado de envío
        """
        config = self.obtener_configuracion()
        
        if not config:
            logger.warning("No hay configuración de notificaciones")
            return {'exitoso': False, 'mensaje': 'No hay configuración'}
        
        resultados = {
            'email': None,
            'telegram': None,
            'exitoso': False
        }
        
        # Enviar por Email
        if config.email_habilitado:
            resultados['email'] = self.enviar_email(
                asunto=asunto,
                mensaje=mensaje,
                evento=evento,
                usuario=usuario,
                destinatarios=destinatarios
            )
        
        # Enviar por Telegram
        if config.telegram_habilitado:
            resultados['telegram'] = self.enviar_telegram(
                mensaje=mensaje,
                evento=evento,
                usuario=usuario
            )
        
        # Determinar si fue exitoso
        resultados['exitoso'] = (
            (resultados['email'] and resultados['email']['exitoso']) or
            (resultados['telegram'] and resultados['telegram']['exitoso'])
        )
        
        return resultados
    
    # ========================================================================
    # NOTIFICACIONES DE EVENTOS ESPECÍFICOS
    # ========================================================================
    
    def notificar_cita_creada(self, cita):
        """Notificar cuando se crea una cita"""
        config = self.obtener_configuracion()
        
        if not config or not config.notificar_cita_creada:
            return
        
        asunto = f"✓ Nueva Cita Creada: {cita.proveedor.razon_social}"
        
        # Mensaje para Email (HTML)
        mensaje_email = f"""
        <h3>Nueva Cita Creada</h3>
        <p><strong>Proveedor:</strong> {cita.proveedor.razon_social}</p>
        <p><strong>Fecha y Hora:</strong> {cita.fecha_cita.strftime('%d/%m/%Y %H:%M')}</p>
        <p><strong>Almacén:</strong> {cita.almacen.nombre}</p>
        <p><strong>Estado:</strong> Programada</p>
        <p><strong>Creado por:</strong> {cita.usuario_creacion.get_full_name() or cita.usuario_creacion.username}</p>
        """
        
        if cita.observaciones:
            mensaje_email += f"<p><strong>Observaciones:</strong> {cita.observaciones}</p>"
        
        # Mensaje para Telegram (Markdown)
        mensaje_telegram = f"""*✓ Nueva Cita Creada*

*Proveedor:* {cita.proveedor.razon_social}
*Fecha y Hora:* {cita.fecha_cita.strftime('%d/%m/%Y %H:%M')}
*Almacén:* {cita.almacen.nombre}
*Estado:* Programada
*Creado por:* {cita.usuario_creacion.get_full_name() or cita.usuario_creacion.username}"""
        
        if cita.observaciones:
            mensaje_telegram += f"\n*Observaciones:* {cita.observaciones}"
        
        return self.enviar_notificacion(
            asunto=asunto,
            mensaje=mensaje_email,  # Para email
            evento='cita_creada',
            usuario=cita.usuario_creacion
        )
    
    def notificar_cita_autorizada(self, cita):
        """Notificar cuando se autoriza una cita"""
        config = self.obtener_configuracion()
        
        if not config or not config.notificar_cita_autorizada:
            return
        
        asunto = f"✓ Cita Autorizada: {cita.proveedor.razon_social}"
        
        # Mensaje para Email (HTML)
        mensaje_email = f"""
        <h3>Cita Autorizada</h3>
        <p><strong>Proveedor:</strong> {cita.proveedor.razon_social}</p>
        <p><strong>Fecha y Hora:</strong> {cita.fecha_cita.strftime('%d/%m/%Y %H:%M')}</p>
        <p><strong>Almacén:</strong> {cita.almacen.nombre}</p>
        <p><strong>Autorizado por:</strong> {cita.usuario_autorizacion.get_full_name() or cita.usuario_autorizacion.username}</p>
        <p><strong>Fecha de Autorización:</strong> {cita.fecha_autorizacion.strftime('%d/%m/%Y %H:%M')}</p>
        """
        
        # Mensaje para Telegram (Markdown)
        mensaje_telegram = f"""*✓ Cita Autorizada*

*Proveedor:* {cita.proveedor.razon_social}
*Fecha y Hora:* {cita.fecha_cita.strftime('%d/%m/%Y %H:%M')}
*Almacén:* {cita.almacen.nombre}
*Autorizado por:* {cita.usuario_autorizacion.get_full_name() or cita.usuario_autorizacion.username}
*Fecha de Autorización:* {cita.fecha_autorizacion.strftime('%d/%m/%Y %H:%M')}"""
        
        return self.enviar_notificacion(
            asunto=asunto,
            mensaje=mensaje_email,
            evento='cita_autorizada',
            usuario=cita.usuario_autorizacion
        )
    
    def notificar_cita_cancelada(self, cita):
        """Notificar cuando se cancela una cita"""
        config = self.obtener_configuracion()
        
        if not config or not config.notificar_cita_cancelada:
            return
        
        asunto = f"✗ Cita Cancelada: {cita.proveedor.razon_social}"
        
        # Mensaje para Email (HTML)
        mensaje_email = f"""
        <h3>Cita Cancelada</h3>
        <p><strong>Proveedor:</strong> {cita.proveedor.razon_social}</p>
        <p><strong>Fecha y Hora (Original):</strong> {cita.fecha_cita.strftime('%d/%m/%Y %H:%M')}</p>
        <p><strong>Almacén:</strong> {cita.almacen.nombre}</p>
        <p><strong>Cancelado por:</strong> {cita.usuario_creacion.get_full_name() or cita.usuario_creacion.username}</p>
        """
        
        # Mensaje para Telegram (Markdown)
        mensaje_telegram = f"""*✗ Cita Cancelada*

*Proveedor:* {cita.proveedor.razon_social}
*Fecha y Hora (Original):* {cita.fecha_cita.strftime('%d/%m/%Y %H:%M')}
*Almacén:* {cita.almacen.nombre}
*Cancelado por:* {cita.usuario_creacion.get_full_name() or cita.usuario_creacion.username}"""
        
        return self.enviar_notificacion(
            asunto=asunto,
            mensaje=mensaje_email,
            evento='cita_cancelada',
            usuario=cita.usuario_creacion
        )



    def notificar_traslado_logistica_asignada(self, orden):
        """Notificar cuando se asigna logística a un traslado"""
        asunto = f"Logística Asignada: {orden.folio}"
        mensaje = f"Se ha asignado logística a la orden {orden.folio}"
        return self.enviar_notificacion(
            asunto=asunto,
            mensaje=mensaje,
            evento='traslado_logistica_asignada',
            usuario=orden.usuario_creacion
        )
    
    def notificar_traslado_iniciado(self, orden):
        """Notificar cuando un traslado inicia"""
        asunto = f"Traslado Iniciado: {orden.folio}"
        mensaje = f"El traslado {orden.folio} ha iniciado"
        return self.enviar_notificacion(
            asunto=asunto,
            mensaje=mensaje,
            evento='traslado_iniciado',
            usuario=orden.usuario_creacion
        )
    
    def notificar_traslado_recibido(self, orden):
        """Notificar cuando se recibe un traslado"""
        asunto = f"Traslado Recibido: {orden.folio}"
        mensaje = f"El traslado {orden.folio} ha sido recibido"
        return self.enviar_notificacion(
            asunto=asunto,
            mensaje=mensaje,
            evento='traslado_recibido',
            usuario=orden.usuario_creacion
        )
    
    def notificar_traslado_completado(self, orden):
        """Notificar cuando un traslado se completa"""
        asunto = f"Traslado Completado: {orden.folio}"
        mensaje = f"El traslado {orden.folio} ha sido completado"
        return self.enviar_notificacion(
            asunto=asunto,
            mensaje=mensaje,
            evento='traslado_completado',
            usuario=orden.usuario_creacion
        )
    
    def notificar_traslado_cancelado(self, orden):
        """Notificar cuando un traslado es cancelado"""
        asunto = f"Traslado Cancelado: {orden.folio}"
        mensaje = f"El traslado {orden.folio} ha sido cancelado"
        return self.enviar_notificacion(
            asunto=asunto,
            mensaje=mensaje,
            evento='traslado_cancelado',
            usuario=orden.usuario_creacion
        )


    def notificar_conteo_completado(self, conteo):
        """Notificar cuando un conteo físico se completa"""
        asunto = f"Conteo Físico Completado: {conteo.folio}"
        mensaje = f"El conteo físico {conteo.folio} ha sido completado"
        return self.enviar_notificacion(
            asunto=asunto,
            mensaje=mensaje,
            evento='conteo_completado',
            usuario=conteo.usuario_creacion
        )

# Instancia global del servicio
notificaciones = ServicioNotificaciones()
