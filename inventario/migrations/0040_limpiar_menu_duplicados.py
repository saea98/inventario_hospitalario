# Generated migration to clean duplicate MenuItemRol entries

from django.db import migrations
from django.db.models import Count, Q


def limpiar_duplicados(apps, schema_editor):
    """Limpiar MenuItemRol duplicados"""
    MenuItemRol = apps.get_model('inventario', 'MenuItemRol')
    
    # Encontrar duplicados
    duplicados = MenuItemRol.objects.values('url_name').annotate(
        count=Count('id')
    ).filter(count__gt=1)
    
    for dup in duplicados:
        url_name = dup['url_name']
        items = MenuItemRol.objects.filter(url_name=url_name).order_by('id')
        
        # Mantener el primero y eliminar los demás
        if items.count() > 1:
            primer_item = items.first()
            items_a_eliminar = items.exclude(id=primer_item.id)
            items_a_eliminar.delete()


def revertir(apps, schema_editor):
    """No hacer nada al revertir"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0038_merge_20260103_2058'),
    ]

    operations = [
        migrations.RunPython(limpiar_duplicados, revertir),
    ]
