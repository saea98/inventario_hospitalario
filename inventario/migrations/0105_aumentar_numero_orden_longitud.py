# Migración para soportar números de orden largos en carga masiva Excel

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0104_citaproveedor_no_es_material_medico'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ordensuministro',
            name='numero_orden',
            field=models.CharField(max_length=200, unique=True),
        ),
    ]
