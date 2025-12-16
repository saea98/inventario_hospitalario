# Generated migration for adding almacen field to User model

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0020_configuracionnotificaciones_lognotificaciones'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='almacen',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='usuarios',
                to='inventario.almacen',
                verbose_name='Almacén Asignado'
            ),
        ),
    ]
