# Generated migration to update criteria 5 and 6 to N/A

from django.db import migrations

def update_criterios_na(apps, schema_editor):
    """Actualizar criterios 5 y 6 a N/A"""
    ItemRevision = apps.get_model('inventario', 'ItemRevision')
    
    # Actualizar criterios 5 y 6 a N/A
    ItemRevision.objects.filter(orden__in=[5, 6]).update(resultado='na')

def reverse_update(apps, schema_editor):
    """Revertir cambios"""
    ItemRevision = apps.get_model('inventario', 'ItemRevision')
    
    # Revertir a SI
    ItemRevision.objects.filter(orden__in=[5, 6]).update(resultado='si')

class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0020_configuracionnotificaciones_lognotificaciones'),
    ]

    operations = [
        migrations.RunPython(update_criterios_na, reverse_update),
    ]
