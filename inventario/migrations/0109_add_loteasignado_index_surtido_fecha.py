from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0108_add_estado_movimientoinventario'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='loteasignado',
            index=models.Index(
                fields=['surtido', 'fecha_asignacion'],
                name='loteasignado_surtido_fecha',
            ),
        ),
    ]
