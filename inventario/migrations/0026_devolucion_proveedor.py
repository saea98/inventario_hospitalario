# Generated migration for DevolucionProveedor and ItemDevolucion models

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0024_llegadaproveedor_itemllegada_documentollegada_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='DevolucionProveedor',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('folio', models.CharField(max_length=50, unique=True)),
                ('estado', models.CharField(choices=[('PENDIENTE', 'Pendiente'), ('AUTORIZADA', 'Autorizada'), ('COMPLETADA', 'Completada'), ('CANCELADA', 'Cancelada'), ('RECHAZADA', 'Rechazada')], default='PENDIENTE', max_length=20)),
                ('motivo_general', models.CharField(choices=[('DEFECTUOSO', 'Producto Defectuoso'), ('CADUCADO', 'Producto Caducado'), ('INCORRECTO', 'Producto Incorrecto'), ('CANTIDAD_INCORRECTA', 'Cantidad Incorrecta'), ('EMBALAJE_DAÑADO', 'Embalaje Dañado'), ('NO_CONFORME', 'No Conforme con Especificaciones'), ('SOLICITUD_CLIENTE', 'Solicitud del Cliente'), ('OTROS', 'Otros')], max_length=50)),
                ('descripcion', models.TextField(blank=True, null=True)),
                ('contacto_proveedor', models.CharField(blank=True, max_length=100, null=True)),
                ('telefono_proveedor', models.CharField(blank=True, max_length=20, null=True)),
                ('email_proveedor', models.EmailField(blank=True, max_length=254, null=True)),
                ('fecha_entrega_estimada', models.DateField(blank=True, null=True)),
                ('numero_autorizacion', models.CharField(blank=True, max_length=50, null=True, unique=True)),
                ('fecha_autorizacion', models.DateTimeField(blank=True, null=True)),
                ('fecha_entrega_real', models.DateField(blank=True, null=True)),
                ('numero_guia', models.CharField(blank=True, max_length=100, null=True)),
                ('empresa_transporte', models.CharField(blank=True, max_length=100, null=True)),
                ('numero_nota_credito', models.CharField(blank=True, max_length=50, null=True, unique=True)),
                ('fecha_nota_credito', models.DateField(blank=True, null=True)),
                ('monto_nota_credito', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('motivo_cancelacion', models.TextField(blank=True, null=True)),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('fecha_actualizacion', models.DateTimeField(auto_now=True)),
                ('institucion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='inventario.institucion')),
                ('proveedor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='inventario.proveedor')),
                ('usuario_autorizo', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='devoluciones_autorizadas', to=settings.AUTH_USER_MODEL)),
                ('usuario_creacion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='devoluciones_creadas', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Devolución de Proveedor',
                'verbose_name_plural': 'Devoluciones de Proveedores',
                'ordering': ['-fecha_creacion'],
            },
        ),
        migrations.CreateModel(
            name='ItemDevolucion',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('cantidad', models.PositiveIntegerField()),
                ('precio_unitario', models.DecimalField(decimal_places=2, max_digits=12)),
                ('motivo_especifico', models.TextField(blank=True, null=True)),
                ('inspeccionado', models.BooleanField(default=False)),
                ('fecha_inspeccion', models.DateTimeField(blank=True, null=True)),
                ('observaciones_inspeccion', models.TextField(blank=True, null=True)),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('devolucion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='inventario.devolucionproveedor')),
                ('lote', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='inventario.lote')),
                ('usuario_inspeccion', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Item de Devolución',
                'verbose_name_plural': 'Items de Devolución',
                'ordering': ['devolucion', 'fecha_creacion'],
            },
        ),
        migrations.AddField(
            model_name='devolucionproveedor',
            name='lotes',
            field=models.ManyToManyField(through='inventario.ItemDevolucion', to='inventario.lote'),
        ),
    ]
