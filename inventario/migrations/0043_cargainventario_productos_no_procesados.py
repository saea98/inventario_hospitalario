# Generated migration to add fields for tracking unprocessed products

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0042_add_registro_conteo_fisico'),
    ]

    operations = [
        migrations.AddField(
            model_name='cargainventario',
            name='productos_no_procesados',
            field=models.JSONField(blank=True, default=list, help_text='Lista de claves CNIS no procesadas', null=True),
        ),
        migrations.AddField(
            model_name='cargainventario',
            name='total_no_procesados',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='cargainventario',
            name='total_productos_sistema',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
