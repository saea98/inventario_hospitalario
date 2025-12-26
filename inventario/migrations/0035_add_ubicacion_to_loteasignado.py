# Generated migration for adding ubicacion fields to LoteAsignado

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0034_merge_20251225_1930'),
    ]

    operations = [
        migrations.AddField(
            model_name='loteasignado',
            name='ubicacion',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='lotes_asignados', to='inventario.ubicacionalmacen', verbose_name='Ubicación del Lote'),
        ),
        migrations.AddField(
            model_name='loteasignado',
            name='cantidad_en_ubicacion',
            field=models.PositiveIntegerField(default=0, verbose_name='Cantidad Disponible en Ubicación'),
        ),
    ]
