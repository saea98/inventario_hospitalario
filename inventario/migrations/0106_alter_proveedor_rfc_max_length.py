# Migración para RFC con guiones (evitar truncar 2 caracteres en reporte inventario detallado)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0105_aumentar_numero_orden_longitud'),
    ]

    operations = [
        migrations.AlterField(
            model_name='proveedor',
            name='rfc',
            field=models.CharField(max_length=20, unique=True, verbose_name='RFC'),
        ),
    ]
