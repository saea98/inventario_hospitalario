# Generated migration - Fake migration for existing tables

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0027_create_devolucion_tables'),
    ]

    operations = [
        # Crear tabla SalidaExistencias (ya existe en la BD)
        migrations.CreateModel(
            name='SalidaExistencias',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('folio', models.CharField(editable=False, max_length=50, unique=True, verbose_name='Folio')),
                ('estado', models.CharField(choices=[('PENDIENTE', 'Pendiente'), ('AUTORIZADA', 'Autorizada'), ('COMPLETADA', 'Completada'), ('CANCELADA', 'Cancelada')], default='PENDIENTE', max_length=20, verbose_name='Estado')),
                ('fecha_salida_estimada', models.DateField(verbose_name='Fecha de Salida Estimada')),
                ('fecha_salida_real', models.DateField(blank=True, null=True, verbose_name='Fecha de Salida Real')),
                ('responsable_salida', models.CharField(max_length=100, verbose_name='Responsable de Salida')),
                ('telefono_responsable', models.CharField(blank=True, max_length=20, verbose_name='Teléfono del Responsable')),
                ('email_responsable', models.EmailField(blank=True, max_length=254, verbose_name='Email del Responsable')),
                ('observaciones', models.TextField(blank=True, verbose_name='Observaciones')),
                ('numero_autorizacion', models.CharField(blank=True, max_length=50, null=True, unique=True, verbose_name='Número de Autorización')),
                ('fecha_autorizacion', models.DateTimeField(blank=True, null=True, verbose_name='Fecha de Autorización')),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Creación')),
                ('fecha_actualizacion', models.DateTimeField(auto_now=True, verbose_name='Fecha de Actualización')),
                ('almacen', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='inventario.almacen', verbose_name='Almacén')),
                ('institucion', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='inventario.institucion', verbose_name='Institución')),
                ('tipo_entrega', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='inventario.tipoentrega', verbose_name='Tipo de Entrega')),
                ('usuario_autorizo', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='salidas_autorizadas', to=settings.AUTH_USER_MODEL, verbose_name='Usuario que Autorizó')),
                ('usuario_creacion', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='salidas_creadas', to=settings.AUTH_USER_MODEL, verbose_name='Usuario que Crea')),
            ],
            options={
                'verbose_name': 'Salida de Existencias',
                'verbose_name_plural': 'Salidas de Existencias',
                'db_table': 'inventario_salidaexistencias',
                'ordering': ['-fecha_creacion'],
            },
        ),
        
        # Crear tabla ItemSalidaExistencias (ya existe en la BD)
        migrations.CreateModel(
            name='ItemSalidaExistencias',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('cantidad', models.PositiveIntegerField(verbose_name='Cantidad')),
                ('precio_unitario', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Precio Unitario')),
                ('observaciones', models.TextField(blank=True, verbose_name='Observaciones')),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('lote', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='inventario.lote', verbose_name='Lote')),
                ('salida', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='itemsalidaexistencias_set', to='inventario.salidaexistencias')),
            ],
            options={
                'verbose_name': 'Item de Salida',
                'verbose_name_plural': 'Items de Salida',
                'db_table': 'inventario_itemsalidaexistencias',
            },
        ),
    ]
