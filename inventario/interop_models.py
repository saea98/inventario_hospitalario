"""
Consumidores de la API de interoperabilidad (equipos externos).

La clave en claro solo se muestra al crearla; en BD se guarda el hash SHA-256.
"""

from __future__ import annotations

import hashlib
import secrets

from django.db import models
from django.utils import timezone


class ApiConsumidor(models.Model):
    SCOPE_EXISTENCIAS = 'existencias:read'
    SCOPE_PRODUCTOS = 'productos:read'
    SCOPE_LOTES = 'lotes:read'
    SCOPE_ALMACENES = 'almacenes:read'
    SCOPES_CHOICES = [
        (SCOPE_EXISTENCIAS, 'Lectura de existencias'),
        (SCOPE_PRODUCTOS, 'Lectura de productos'),
        (SCOPE_LOTES, 'Lectura de lotes'),
        (SCOPE_ALMACENES, 'Lectura de almacenes'),
    ]
    SCOPES_DEFAULT = [
        SCOPE_EXISTENCIAS,
        SCOPE_PRODUCTOS,
        SCOPE_LOTES,
        SCOPE_ALMACENES,
    ]

    nombre = models.CharField(max_length=120, verbose_name='Nombre del equipo / sistema')
    descripcion = models.TextField(blank=True, default='')
    key_prefix = models.CharField(max_length=12, db_index=True, editable=False)
    key_hash = models.CharField(max_length=64, unique=True, editable=False)
    activo = models.BooleanField(default=True)
    scopes = models.JSONField(
        default=list,
        blank=True,
        help_text='Lista de scopes, p.ej. ["existencias:read","productos:read","lotes:read"]',
    )
    institucion = models.ForeignKey(
        'inventario.Institucion',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='api_consumidores',
        help_text='Si se define, las consultas se restringen a esa institución.',
    )
    contacto = models.CharField(max_length=200, blank=True, default='')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    ultimo_uso = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'API consumidor (interop)'
        verbose_name_plural = 'API consumidores (interop)'
        ordering = ['nombre']

    def __str__(self):
        estado = 'activo' if self.activo else 'inactivo'
        return f'{self.nombre} ({self.key_prefix}…, {estado})'

    def tiene_scope(self, scope: str) -> bool:
        scopes = self.scopes or []
        return scope in scopes or '*' in scopes

    def marcar_uso(self):
        ApiConsumidor.objects.filter(pk=self.pk).update(ultimo_uso=timezone.now())

    @staticmethod
    def hash_key(raw_key: str) -> str:
        return hashlib.sha256(raw_key.encode('utf-8')).hexdigest()

    @classmethod
    def generar_clave(cls) -> str:
        # Prefijo legible para soporte; el secreto completo es url-safe.
        return f'ih_{secrets.token_urlsafe(32)}'

    @classmethod
    def crear_con_clave(cls, **kwargs):
        """
        Crea el consumidor y devuelve (instancia, clave_en_claro).
        La clave en claro no se vuelve a mostrar.
        """
        raw = cls.generar_clave()
        kwargs = dict(kwargs)
        kwargs.setdefault('scopes', list(cls.SCOPES_DEFAULT))
        kwargs['key_prefix'] = raw[:10]
        kwargs['key_hash'] = cls.hash_key(raw)
        obj = cls.objects.create(**kwargs)
        return obj, raw

    @classmethod
    def autenticar(cls, raw_key: str):
        if not raw_key:
            return None
        raw_key = raw_key.strip()
        digest = cls.hash_key(raw_key)
        return cls.objects.filter(activo=True, key_hash=digest).select_related('institucion').first()
