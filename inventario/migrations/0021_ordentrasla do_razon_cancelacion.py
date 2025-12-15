# Generated migration using SQL for adding razon_cancelacion field

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0020_configuracionnotificaciones_lognotificaciones'),
    ]

    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE inventario_ordentrasla do ADD COLUMN razon_cancelacion TEXT NULL;",
            reverse_sql="ALTER TABLE inventario_ordentrasla do DROP COLUMN razon_cancelacion;",
        ),
    ]
