# Generated migration for Fase 4: Distribución a Áreas

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0027_create_devolucion_tables'),
    ]

    operations = [
        # Crear tabla DistribucionArea
        migrations.CreateModel(
            name='DistribucionArea',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('area_destino', models.CharField(max_length=100, verbose_name='Área de Destino')),
                ('responsable_area', models.CharField(max_length=100, verbose_name='Responsable del Área')),
                ('telefono_responsable', models.CharField(blank=True, max_length=20, verbose_name='Teléfono')),
                ('email_responsable', models.EmailField(blank=True, max_length=254, verbose_name='Email')),
                ('estado', models.CharField(choices=[('PENDIENTE', 'Pendiente'), ('EN_TRANSITO', 'En Tránsito'), ('ENTREGADA', 'Entregada'), ('RECHAZADA', 'Rechazada')], default='PENDIENTE', max_length=20, verbose_name='Estado')),
                ('fecha_entrega_estimada', models.DateField(verbose_name='Fecha de Entrega Estimada')),
                ('fecha_entrega_real', models.DateField(blank=True, null=True, verbose_name='Fecha de Entrega Real')),
                ('recibido_por', models.CharField(blank=True, max_length=100, verbose_name='Recibido por')),
                ('firma_recibido', models.TextField(blank=True, verbose_name='Firma (Base64)')),
                ('observaciones_entrega', models.TextField(blank=True, verbose_name='Observaciones de Entrega')),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('fecha_actualizacion', models.DateTimeField(auto_now=True)),
                ('salida', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='distribuciones', to='inventario.salidaexistencias')),
                ('usuario_creacion', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='distribuciones_creadas', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Distribución a Área',
                'verbose_name_plural': 'Distribuciones a Áreas',
                'db_table': 'inventario_distribucionarea',
                'ordering': ['-fecha_creacion'],
            },
        ),
        
        # Crear tabla ItemDistribucion
        migrations.CreateModel(
            name='ItemDistribucion',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('cantidad', models.PositiveIntegerField(verbose_name='Cantidad Distribuida')),
                ('precio_unitario', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Precio Unitario')),
                ('observaciones', models.TextField(blank=True, verbose_name='Observaciones')),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('distribucion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='itemdistribucion_set', to='inventario.distribucionarea')),
                ('item_salida', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='inventario.itemsalidaexistencias', verbose_name='Item de Salida')),
            ],
            options={
                'verbose_name': 'Item de Distribución',
                'verbose_name_plural': 'Items de Distribución',
                'db_table': 'inventario_itemdistribucion',
            },
        ),
    ]
