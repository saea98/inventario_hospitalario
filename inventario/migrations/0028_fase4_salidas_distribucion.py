# Generated migration for Fase 4: Gestión de Salidas y Distribución

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0027_create_devolucion_tables'),
    ]

    operations = [
        # Crear tabla SalidaExistencias
        migrations.CreateModel(
            name='SalidaExistencias',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('folio', models.CharField(editable=False, max_length=50, unique=True)),
                ('estado', models.CharField(choices=[('PENDIENTE', 'Pendiente'), ('AUTORIZADA', 'Autorizada'), ('COMPLETADA', 'Completada'), ('CANCELADA', 'Cancelada')], default='PENDIENTE', max_length=20)),
                ('tipo_entrega', models.CharField(max_length=100)),
                ('responsable_salida', models.CharField(max_length=150)),
                ('telefono_responsable', models.CharField(blank=True, max_length=20, null=True)),
                ('correo_responsable', models.EmailField(blank=True, max_length=254, null=True)),
                ('numero_autorizacion', models.CharField(blank=True, max_length=100, null=True, unique=True)),
                ('motivo_cancelacion', models.TextField(blank=True, null=True)),
                ('observaciones', models.TextField(blank=True, null=True)),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('fecha_autorizacion', models.DateTimeField(blank=True, null=True)),
                ('fecha_cancelacion', models.DateTimeField(blank=True, null=True)),
                ('almacen', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='inventario.almacen')),
                ('institucion', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='inventario.institucion')),
                ('usuario_creacion', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='salidas_creadas', to=settings.AUTH_USER_MODEL)),
                ('usuario_autorizo', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='salidas_autorizadas', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Salida de Existencias',
                'verbose_name_plural': 'Salidas de Existencias',
                'ordering': ['-fecha_creacion'],
            },
        ),
        
        # Crear tabla ItemSalidaExistencias
        migrations.CreateModel(
            name='ItemSalidaExistencias',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('cantidad', models.PositiveIntegerField()),
                ('precio_unitario', models.DecimalField(decimal_places=2, max_digits=10)),
                ('observaciones', models.TextField(blank=True, null=True)),
                ('lote', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='inventario.lote')),
                ('salida', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='itemsalidaexistencias', to='inventario.salidaexistencias')),
            ],
            options={
                'verbose_name': 'Item de Salida',
                'verbose_name_plural': 'Items de Salida',
            },
        ),
        
        # Crear tabla DistribucionArea
        migrations.CreateModel(
            name='DistribucionArea',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('area_destino', models.CharField(max_length=150)),
                ('responsable_area', models.CharField(max_length=150)),
                ('telefono_area', models.CharField(blank=True, max_length=20, null=True)),
                ('correo_area', models.EmailField(blank=True, max_length=254, null=True)),
                ('estado', models.CharField(choices=[('PENDIENTE', 'Pendiente'), ('EN_TRANSITO', 'En Tránsito'), ('ENTREGADA', 'Entregada'), ('RECHAZADA', 'Rechazada')], default='PENDIENTE', max_length=20)),
                ('fecha_entrega_estimada', models.DateField(blank=True, null=True)),
                ('fecha_entrega_real', models.DateTimeField(blank=True, null=True)),
                ('motivo_rechazo', models.TextField(blank=True, null=True)),
                ('observaciones', models.TextField(blank=True, null=True)),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('salida', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='distribuciones', to='inventario.salidaexistencias')),
            ],
            options={
                'verbose_name': 'Distribución a Área',
                'verbose_name_plural': 'Distribuciones a Áreas',
                'ordering': ['-fecha_creacion'],
            },
        ),
        
        # Crear tabla ItemDistribucion
        migrations.CreateModel(
            name='ItemDistribucion',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('cantidad', models.PositiveIntegerField()),
                ('precio_unitario', models.DecimalField(decimal_places=2, max_digits=10)),
                ('observaciones', models.TextField(blank=True, null=True)),
                ('distribucion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='itemdistribucion', to='inventario.distribucionarea')),
                ('item_salida', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='inventario.itemsalidaexistencias')),
            ],
            options={
                'verbose_name': 'Item de Distribución',
                'verbose_name_plural': 'Items de Distribución',
            },
        ),
        
        # Crear índices
        migrations.AddIndex(
            model_name='salidaexistencias',
            index=models.Index(fields=['institucion', 'estado'], name='inventario_salidaexistencias_institucion_estado_idx'),
        ),
        migrations.AddIndex(
            model_name='salidaexistencias',
            index=models.Index(fields=['almacen', 'fecha_creacion'], name='inventario_salidaexistencias_almacen_fecha_idx'),
        ),
        migrations.AddIndex(
            model_name='distribucionarea',
            index=models.Index(fields=['salida', 'estado'], name='inventario_distribucionarea_salida_estado_idx'),
        ),
    ]
