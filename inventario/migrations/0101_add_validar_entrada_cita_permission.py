# Generated migration for adding validar_entrada_cita permission

from django.db import migrations


def add_permission(apps, schema_editor):
    """Agregar permiso personalizado validar_entrada_cita"""
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType
    
    # Obtener el ContentType de CitaProveedor
    cita_content_type = ContentType.objects.get(app_label='inventario', model='citaproveedor')
    
    # Crear el permiso si no existe
    permission, created = Permission.objects.get_or_create(
        codename='validar_entrada_cita',
        content_type=cita_content_type,
        defaults={'name': 'Puede validar entrada de cita'}
    )
    
    if created:
        print(f"✓ Permiso 'validar_entrada_cita' creado exitosamente")
    else:
        print(f"✓ Permiso 'validar_entrada_cita' ya existe")


def remove_permission(apps, schema_editor):
    """Remover permiso personalizado validar_entrada_cita"""
    from django.contrib.auth.models import Permission
    
    Permission.objects.filter(codename='validar_entrada_cita').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0100_citaproveedor_detalles_json'),
    ]

    operations = [
        migrations.RunPython(add_permission, remove_permission),
    ]
