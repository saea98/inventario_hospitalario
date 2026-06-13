from django.core.validators import MinValueValidator
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0110_transferenciaentrada'),
    ]

    operations = [
        migrations.AddField(
            model_name='itemtransferenciaentrada',
            name='precio_unitario_sin_iva',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=12,
                null=True,
                validators=[MinValueValidator(0)],
            ),
        ),
        migrations.AddField(
            model_name='itemtransferenciaentrada',
            name='porcentaje_iva',
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                max_digits=5,
                validators=[MinValueValidator(0)],
            ),
        ),
        migrations.AddField(
            model_name='itemtransferenciaentrada',
            name='precio_unitario_con_iva',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=12,
                null=True,
                validators=[MinValueValidator(0)],
            ),
        ),
        migrations.AddField(
            model_name='itemtransferenciaentrada',
            name='subtotal',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=15,
                null=True,
                validators=[MinValueValidator(0)],
            ),
        ),
        migrations.AddField(
            model_name='itemtransferenciaentrada',
            name='importe_iva',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=15,
                null=True,
                validators=[MinValueValidator(0)],
            ),
        ),
        migrations.AddField(
            model_name='itemtransferenciaentrada',
            name='importe_total',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=15,
                null=True,
                validators=[MinValueValidator(0)],
            ),
        ),
    ]
