from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import json


class LogSistema(models.Model):
    """Modelo para almacenar logs del sistema"""
    
    NIVEL_CHOICES = [
        ('DEBUG', 'Debug'),
        ('INFO', 'Información'),
        ('WARNING', 'Advertencia'),
        ('ERROR', 'Error'),
        ('CRITICAL', 'Crítico'),
    ]
    
    TIPO_CHOICES = [
        ('ESTATICO', 'Archivo Estático'),
        ('BASE_DATOS', 'Base de Datos'),
        ('AUTENTICACION', 'Autenticación'),
        ('NEGOCIO', 'Lógica de Negocio'),
        ('SISTEMA', 'Sistema'),
        ('SEGURIDAD', 'Seguridad'),
        ('OTRO', 'Otro'),
    ]
    
    nivel = models.CharField(
        max_length=10,
        choices=NIVEL_CHOICES,
        default='INFO',
        db_index=True
    )
    
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        default='OTRO',
        db_index=True
    )
    
    titulo = models.CharField(max_length=255, db_index=True)
    
    mensaje = models.TextField()
    
    # Detalles adicionales en JSON
    detalles = models.JSONField(default=dict, blank=True)
    
    # Usuario que causó el error (opcional)
    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='logs_sistema'
    )
    
    # URL donde ocurrió el error
    url = models.CharField(max_length=500, blank=True, null=True)
    
    # IP del cliente
    ip_cliente = models.GenericIPAddressField(blank=True, null=True)
    
    # User Agent
    user_agent = models.TextField(blank=True)
    
    fecha_creacion = models.DateTimeField(auto_now_add=True, db_index=True)
    
    # Para marcar como resuelto
    resuelto = models.BooleanField(default=False, db_index=True)
    
    fecha_resolucion = models.DateTimeField(null=True, blank=True)
    
    notas_resolucion = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Log del Sistema'
        verbose_name_plural = 'Logs del Sistema'
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['-fecha_creacion', 'nivel']),
            models.Index(fields=['-fecha_creacion', 'tipo']),
            models.Index(fields=['resuelto', '-fecha_creacion']),
        ]
    
    def __str__(self):
        return f"[{self.nivel}] {self.titulo} - {self.fecha_creacion.strftime('%d/%m/%Y %H:%M')}"
    
    @classmethod
    def crear_log(cls, nivel, tipo, titulo, mensaje, usuario=None, url=None, 
                  ip_cliente=None, user_agent=None, detalles=None):
        """Método helper para crear logs fácilmente"""
        return cls.objects.create(
            nivel=nivel,
            tipo=tipo,
            titulo=titulo,
            mensaje=mensaje,
            usuario=usuario,
            url=url,
            ip_cliente=ip_cliente,
            user_agent=user_agent,
            detalles=detalles or {}
        )
    
    @classmethod
    def error_estatico(cls, archivo, razon, usuario=None, url=None, ip_cliente=None, user_agent=None):
        """Log para errores de archivos estáticos"""
        return cls.crear_log(
            nivel='ERROR',
            tipo='ESTATICO',
            titulo=f'Error al cargar: {archivo}',
            mensaje=f'No se pudo cargar el archivo estático: {archivo}. Razón: {razon}',
            usuario=usuario,
            url=url,
            ip_cliente=ip_cliente,
            user_agent=user_agent,
            detalles={'archivo': archivo, 'razon': razon}
        )
    
    def marcar_resuelto(self, notas=''):
        """Marcar el log como resuelto"""
        self.resuelto = True
        self.fecha_resolucion = timezone.now()
        self.notas_resolucion = notas
        self.save()
