# Generated migration for LogErrorPedido model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0025_merge_0024_migrations'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='LogErrorPedido',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tipo_error', models.CharField(
                    choices=[
                        ('CLAVE_NO_EXISTE', 'Clave no existe'),
                        ('SIN_EXISTENCIA', 'Sin existencia disponible'),
                        ('CANTIDAD_INVALIDA', 'Cantidad inválida'),
                        ('OTRO', 'Otro error'),
                    ],
                    max_length=20,
                    verbose_name='Tipo de Error'
                )),
                ('clave_solicitada', models.CharField(max_length=50, verbose_name='Clave Solicitada')),
                ('cantidad_solicitada', models.PositiveIntegerField(blank=True, null=True, verbose_name='Cantidad Solicitada')),
                ('descripcion_error', models.TextField(verbose_name='Descripción del Error')),
                ('fecha_error', models.DateTimeField(auto_now_add=True, verbose_name='Fecha del Error')),
                ('alerta_enviada', models.BooleanField(default=False, verbose_name='¿Se envió alerta?')),
                ('fecha_alerta', models.DateTimeField(blank=True, null=True, verbose_name='Fecha de Alerta')),
                ('almacen', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='errores_pedidos', to='inventario.almacen', verbose_name='Almacén Destino')),
                ('institucion', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='errores_pedidos', to='inventario.institucion', verbose_name='Institución')),
                ('usuario', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='errores_pedidos', to=settings.AUTH_USER_MODEL, verbose_name='Usuario que Cargó')),
            ],
            options={
                'verbose_name': 'Log de Error en Pedido',
                'verbose_name_plural': 'Logs de Errores en Pedidos',
                'ordering': ['-fecha_error'],
            },
        ),
        migrations.AddIndex(
            model_name='logerrorpedido',
            index=models.Index(fields=['fecha_error'], name='inventario__fecha_e_idx'),
        ),
        migrations.AddIndex(
            model_name='logerrorpedido',
            index=models.Index(fields=['tipo_error'], name='inventario__tipo_er_idx'),
        ),
        migrations.AddIndex(
            model_name='logerrorpedido',
            index=models.Index(fields=['clave_solicitada'], name='inventario__clave_s_idx'),
        ),
    ]
