# Generated migration for Fase 4: Distribución a Áreas

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
            model_name='distribucionarea',
            index=models.Index(fields=['salida', 'estado'], name='inventario_distribucionarea_salida_estado_idx'),
        ),
    ]
