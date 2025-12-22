# Generated migration for making menu_item flexible

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0030_merge_migrations'),
    ]

    operations = [
        migrations.AlterField(
            model_name='menuitemrol',
            name='menu_item',
            field=models.CharField(
                help_text='Identificador único del menú (ej: gestion_proveedores, administracion)',
                max_length=100,
                unique=True,
                verbose_name='Opción de Menú'
            ),
        ),
    ]
