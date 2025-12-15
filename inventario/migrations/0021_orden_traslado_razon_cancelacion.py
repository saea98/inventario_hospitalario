# Generated migration for adding razon_cancelacion field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0020_configuracionnotificaciones_lognotificaciones'),
    ]

    operations = [
        migrations.AddField(
            model_name='ordentrasla do',
            name='razon_cancelacion',
            field=models.TextField(blank=True, null=True, verbose_name='Razón de Cancelación'),
        ),
    ]
