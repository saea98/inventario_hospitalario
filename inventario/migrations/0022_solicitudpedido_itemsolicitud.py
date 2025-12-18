# Generated migration for SolicitudPedido and ItemSolicitud models

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0021_user_almacen'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='SolicitudPedido',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('folio', models.CharField(editable=False, max_length=50, unique=True, verbose_name='Folio de Solicitud')),
                ('fecha_solicitud', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Solicitud')),
                ('fecha_validacion', models.DateTimeField(blank=True, null=True, verbose_name='Fecha de Validación')),
                ('fecha_entrega_programada', models.DateField(verbose_name='Fecha de Entrega Programada')),
                ('estado', models.CharField(choices=[('PENDIENTE', 'Pendiente de Validación'), ('VALIDADA', 'Validada y Aprobada'), ('RECHAZADA', 'Rechazada'), ('EN_PREPARACION', 'En Preparación (Surtimiento)'), ('PREPARADA', 'Preparada para Entrega'), ('ENTREGADA', 'Entregada'), ('CANCELADA', 'Cancelada por Usuario')], default='PENDIENTE', max_length=20, verbose_name='Estado')),
                ('observaciones_solicitud', models.TextField(blank=True, verbose_name='Observaciones de la Solicitud')),
                ('observaciones_validacion', models.TextField(blank=True, verbose_name='Observaciones de la Validación')),
                ('almacen_destino', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='solicitudes_recibidas', to='inventario.almacen', verbose_name='Almacén Destino')),
                ('institucion_solicitante', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='solicitudes_realizadas', to='inventario.institucion', verbose_name='Institución Solicitante')),
                ('usuario_solicitante', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='pedidos_solicitados', to=settings.AUTH_USER_MODEL, verbose_name='Usuario Solicitante')),
                ('usuario_validacion', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='pedidos_validados', to=settings.AUTH_USER_MODEL, verbose_name='Usuario de Validación')),
            ],
            options={
                'verbose_name': 'Solicitud de Pedido',
                'verbose_name_plural': 'Solicitudes de Pedidos',
                'ordering': ['-fecha_solicitud'],
            },
        ),
        migrations.CreateModel(
            name='ItemSolicitud',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('cantidad_solicitada', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1)], verbose_name='Cantidad Solicitada')),
                ('cantidad_aprobada', models.PositiveIntegerField(default=0, verbose_name='Cantidad Aprobada')),
                ('justificacion_cambio', models.CharField(blank=True, max_length=255, verbose_name='Justificación del Cambio')),
                ('producto', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='items_solicitados', to='inventario.producto', verbose_name='Producto')),
                ('solicitud', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='inventario.solicitudpedido', verbose_name='Solicitud')),
            ],
            options={
                'verbose_name': 'Item de Solicitud',
                'verbose_name_plural': 'Items de la Solicitud',
            },
        ),
        migrations.AddConstraint(
            model_name='itemsolicitud',
            constraint=models.UniqueConstraint(fields=('solicitud', 'producto'), name='unique_solicitud_producto'),
        ),
    ]
