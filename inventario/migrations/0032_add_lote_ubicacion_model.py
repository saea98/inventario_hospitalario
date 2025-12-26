# Generated migration for LoteUbicacion model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0031_hacer_menu_item_flexible'),
    ]

    operations = [
        migrations.CreateModel(
            name='LoteUbicacion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cantidad', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1)], verbose_name='Cantidad')),
                ('fecha_asignacion', models.DateTimeField(auto_now_add=True)),
                ('fecha_actualizacion', models.DateTimeField(auto_now=True)),
                ('lote', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ubicaciones_detalle', to='inventario.lote', verbose_name='Lote')),
                ('ubicacion', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='inventario.ubicacionalmacen', verbose_name='Ubicación')),
                ('usuario_asignacion', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='asignaciones_ubicacion', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Ubicación de Lote',
                'verbose_name_plural': 'Ubicaciones de Lotes',
                'ordering': ['lote', 'ubicacion'],
            },
        ),
        migrations.AlterUniqueTogether(
            name='loteubicacion',
            unique_together={('lote', 'ubicacion')},
        ),
    ]
