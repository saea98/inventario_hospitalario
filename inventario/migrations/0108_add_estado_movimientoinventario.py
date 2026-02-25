# Generated manually: la tabla inventario_movimientoinventario no tenía la columna estado

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0107_add_loteasignado_usuario_surtido'),
    ]

    operations = [
        migrations.AddField(
            model_name='movimientoinventario',
            name='estado',
            field=models.IntegerField(default=1),
        ),
    ]
