# Generated manually for entradas por transferencia

import uuid

import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('inventario', '0109_add_loteasignado_index_surtido_fecha'),
    ]

    operations = [
        migrations.CreateModel(
            name='TransferenciaEntrada',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('folio', models.CharField(db_index=True, max_length=50, unique=True)),
                ('remision', models.CharField(max_length=100, verbose_name='Remisión')),
                ('entidad_origen', models.CharField(help_text='Ej. Almacén Vallejo, Jalisco, etc.', max_length=255, verbose_name='Almacén / entidad origen')),
                ('estado_origen', models.CharField(blank=True, max_length=100, verbose_name='Estado (origen)')),
                ('fecha_recepcion', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Fecha de recepción')),
                ('numero_piezas_recibidas', models.PositiveIntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0)], verbose_name='Piezas recibidas (total)')),
                ('observaciones', models.TextField(blank=True)),
                ('estado', models.CharField(choices=[('EN_RECEPCION', 'En Recepción'), ('UBICACION', 'Asignando Ubicación'), ('APROBADA', 'Aprobada'), ('CANCELADA', 'Cancelada')], default='EN_RECEPCION', max_length=20)),
                ('fecha_aprobacion', models.DateTimeField(blank=True, null=True)),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('fecha_actualizacion', models.DateTimeField(auto_now=True)),
                ('almacen_destino', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='transferencias_recibidas', to='inventario.almacen', verbose_name='Almacén destino')),
                ('creado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='transferencias_creadas', to=settings.AUTH_USER_MODEL)),
                ('usuario_aprobacion', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='transferencias_aprobadas', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Entrada por transferencia',
                'verbose_name_plural': 'Entradas por transferencia',
                'ordering': ['-fecha_creacion'],
                'permissions': [('aprobar_transferenciaentrada', 'Puede aprobar entradas por transferencia')],
            },
        ),
        migrations.CreateModel(
            name='ItemTransferenciaEntrada',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('clave', models.CharField(max_length=150, verbose_name='Clave CNIS')),
                ('descripcion', models.TextField(blank=True)),
                ('numero_lote', models.CharField(max_length=100, verbose_name='Número de lote')),
                ('fecha_caducidad', models.DateField(blank=True, null=True)),
                ('cantidad_recibida', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1)], verbose_name='Cantidad recibida')),
                ('unidad_medida', models.CharField(default='Pieza', max_length=50)),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('lote_creado', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='item_transferencia', to='inventario.lote')),
                ('producto', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='inventario.producto')),
                ('transferencia', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='inventario.transferenciaentrada')),
            ],
            options={
                'verbose_name': 'Ítem de transferencia',
                'verbose_name_plural': 'Ítems de transferencia',
                'ordering': ['fecha_creacion'],
                'unique_together': {('transferencia', 'numero_lote', 'clave')},
            },
        ),
    ]
