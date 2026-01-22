# Generated migration for adding cantidad_reservada to LoteUbicacion

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0101_add_validar_entrada_cita_permission'),
    ]

    operations = [
        migrations.AddField(
            model_name='loteubicacion',
            name='cantidad_reservada',
            field=models.PositiveIntegerField(default=0, verbose_name='Cantidad Reservada en Propuestas'),
        ),
    ]
