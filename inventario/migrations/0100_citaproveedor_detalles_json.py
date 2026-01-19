# Generated migration

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0099_citaproveedor_cancelacion_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='citaproveedor',
            name='detalles_json',
            field=models.JSONField(blank=True, default=list, help_text='Lista de detalles con remisión y clave de producto en formato JSON', verbose_name='Detalles de la Cita'),
        ),
    ]
