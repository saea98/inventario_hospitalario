# Generated migration for llegada models

from django.db import migrations, models
import django.db.models.deletion
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0021_update_criterios_na'),
    ]

    operations = [
        migrations.AddField(
            model_name='llegadaproveedor',
            name='folio_validacion',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='llegadaproveedor',
            name='almacen',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.PROTECT, related_name='llegadas_proveedor', to='inventario.almacen'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='llegadaproveedor',
            name='tipo_red',
            field=models.CharField(blank=True, choices=[('FRIA', 'Red Fría'), ('SECA', 'Red Seca')], max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='itemllegada',
            name='piezas_por_lote',
            field=models.IntegerField(default=1, validators=[django.core.validators.MinValueValidator(1)]),
        ),
    ]
