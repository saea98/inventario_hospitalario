# Generated migration for Fase 2.2.1 - Gestión de Pedidos y Salida (CORREGIDA)

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0021_user_almacen'),
    ]

    operations = [
        # Crear tabla SolicitudPedido
        migrations.CreateModel(
            name='SolicitudPedido',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('folio', models.CharField(max_length=50, unique=True)),
                ('estado', models.CharField(choices=[('PENDIENTE', 'Pendiente'), ('VALIDADA', 'Validada'), ('PREPARADA', 'Preparada'), ('ENTREGADA', 'Entregada'), ('CANCELADA', 'Cancelada')], default='PENDIENTE', max_length=20)),
                ('fecha_solicitud', models.DateTimeField(auto_now_add=True)),
                ('fecha_validacion', models.DateTimeField(blank=True, null=True)),
                ('fecha_preparacion', models.DateTimeField(blank=True, null=True)),
                ('fecha_entrega', models.DateTimeField(blank=True, null=True)),
                ('fecha_entrega_programada', models.DateField()),
                ('observaciones', models.TextField(blank=True)),
                ('almacen_origen', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='solicitudes_pedido', to='inventario.almacen')),
                ('institucion', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='solicitudes_pedido', to='inventario.institucion')),
                ('usuario_solicitante', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='solicitudes_pedido_creadas', to=settings.AUTH_USER_MODEL)),
                ('usuario_validacion', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='solicitudes_pedido_validadas', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Solicitud de Pedido',
                'verbose_name_plural': 'Solicitudes de Pedidos',
                'ordering': ['-fecha_solicitud'],
            },
        ),

        # Crear tabla ItemSolicitudPedido
        migrations.CreateModel(
            name='ItemSolicitudPedido',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('cantidad_solicitada', models.PositiveIntegerField()),
                ('cantidad_aprobada', models.PositiveIntegerField(default=0)),
                ('estado', models.CharField(choices=[('PENDIENTE', 'Pendiente'), ('VALIDADO', 'Validado'), ('NO_DISPONIBLE', 'No Disponible'), ('PARCIAL', 'Parcial')], default='PENDIENTE', max_length=20)),
                ('lote_asignado', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='inventario.lote')),
                ('producto', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='inventario.producto')),
                ('solicitud', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='inventario.solicitudpedido')),
            ],
            options={
                'verbose_name': 'Item de Solicitud',
                'verbose_name_plural': 'Items de Solicitud',
            },
        ),

        # Crear tabla OrdenSurtimiento
        migrations.CreateModel(
            name='OrdenSurtimiento',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('folio', models.CharField(max_length=50, unique=True)),
                ('fecha_generacion', models.DateTimeField(auto_now_add=True)),
                ('estado', models.CharField(choices=[('GENERADA', 'Generada'), ('EN_PICKING', 'En Picking'), ('COMPLETADA', 'Completada')], default='GENERADA', max_length=20)),
                ('observaciones', models.TextField(blank=True)),
                ('solicitud', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='orden_surtimiento', to='inventario.solicitudpedido')),
            ],
            options={
                'verbose_name': 'Orden de Surtimiento',
                'verbose_name_plural': 'Órdenes de Surtimiento',
                'ordering': ['-fecha_generacion'],
            },
        ),

        # Crear tabla SalidaExistencias
        migrations.CreateModel(
            name='SalidaExistencias',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('folio', models.CharField(max_length=50, unique=True)),
                ('fecha_salida', models.DateTimeField(auto_now_add=True)),
                ('nombre_receptor', models.CharField(max_length=200)),
                ('firma_receptor', models.TextField(blank=True)),
                ('observaciones', models.TextField(blank=True)),
                ('almacen_origen', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='inventario.almacen')),
                ('institucion_destino', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='inventario.institucion')),
                ('solicitud', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='salida_existencias', to='inventario.solicitudpedido')),
                ('usuario_validacion', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Salida de Existencias',
                'verbose_name_plural': 'Salidas de Existencias',
                'ordering': ['-fecha_salida'],
            },
        ),

        # Crear tabla ItemSalidaExistencias
        migrations.CreateModel(
            name='ItemSalidaExistencias',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('cantidad', models.PositiveIntegerField()),
                ('precio_unitario', models.DecimalField(decimal_places=2, max_digits=10)),
                ('importe_total', models.DecimalField(decimal_places=2, max_digits=12)),
                ('lote', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='inventario.lote')),
                ('producto', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='inventario.producto')),
                ('salida', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='inventario.salidaexistencias')),
                ('ubicacion', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='inventario.ubicacionalmacen')),
            ],
            options={
                'verbose_name': 'Item de Salida',
                'verbose_name_plural': 'Items de Salida',
            },
        ),
    ]
