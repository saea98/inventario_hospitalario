# Generated manually - Bandera "No es material médico" en Cita de Proveedor

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0103_add_producto_no_disponible_almacen'),
    ]

    operations = [
        migrations.AddField(
            model_name='citaproveedor',
            name='no_es_material_medico',
            field=models.BooleanField(
                default=False,
                help_text='Marcar cuando la cita corresponde a material que no es médico',
                verbose_name='No es material médico',
            ),
        ),
    ]
