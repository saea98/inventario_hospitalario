from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0052_add_llegada_fields'),
    ]

    operations = [
        # Primero agregamos el campo como nullable
        migrations.AddField(
            model_name='llegadaproveedor',
            name='almacen_temp',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='llegadas_proveedor_temp', to='inventario.almacen'),
        ),
        # Luego copiamos datos de la cita si existen
        migrations.RunPython(
            code=lambda apps, schema_editor: None,  # No hacer nada en forward
            reverse_code=lambda apps, schema_editor: None,  # No hacer nada en reverse
        ),
        # Renombramos el campo
        migrations.RenameField(
            model_name='llegadaproveedor',
            old_name='almacen_temp',
            new_name='almacen',
        ),
    ]
