# Generated migration for RegistroConteoFisico model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('inventario', '0041_merge_0039_logsistema_0040_limpiar_menu_duplicados'),
    ]

    operations = [
        migrations.CreateModel(
            name='RegistroConteoFisico',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('primer_conteo', models.PositiveIntegerField(blank=True, null=True, verbose_name='Primer Conteo')),
                ('segundo_conteo', models.PositiveIntegerField(blank=True, null=True, verbose_name='Segundo Conteo')),
                ('tercer_conteo', models.PositiveIntegerField(blank=True, null=True, verbose_name='Tercer Conteo (Definitivo)')),
                ('observaciones', models.TextField(blank=True, null=True, verbose_name='Observaciones')),
                ('completado', models.BooleanField(default=False, help_text='Se marca como completado cuando se guarda el tercer conteo', verbose_name='Conteo Completado')),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True, verbose_name='Fecha Creación')),
                ('fecha_actualizacion', models.DateTimeField(auto_now=True, verbose_name='Fecha Actualización')),
                ('lote_ubicacion', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='registro_conteo', to='inventario.loteubicacion', verbose_name='Lote Ubicación')),
                ('usuario_creacion', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='registros_conteo_creados', to=settings.AUTH_USER_MODEL, verbose_name='Usuario Creación')),
                ('usuario_ultima_actualizacion', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='registros_conteo_actualizados', to=settings.AUTH_USER_MODEL, verbose_name='Usuario Última Actualización')),
            ],
            options={
                'verbose_name': 'Registro de Conteo Físico',
                'verbose_name_plural': 'Registros de Conteo Físico',
                'ordering': ['-fecha_actualizacion'],
            },
        ),
    ]
