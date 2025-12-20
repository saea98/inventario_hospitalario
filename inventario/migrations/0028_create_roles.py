from django.db import migrations
from django.contrib.auth.models import Group

def create_roles(apps, schema_editor):
    """
    Crea los roles (grupos) necesarios para el sistema de inventario
    basados en el Manual de Procedimientos del Almacén
    """
    roles = [
        {
            'name': 'Revisión',
            'description': 'Responsable de revisar y autorizar citas y pedidos'
        },
        {
            'name': 'Almacenero',
            'description': 'Responsable de recepción, almacenamiento y picking'
        },
        {
            'name': 'Control Calidad',
            'description': 'Responsable de inspeccionar productos'
        },
        {
            'name': 'Facturación',
            'description': 'Responsable de registrar facturas'
        },
        {
            'name': 'Supervisión',
            'description': 'Responsable de supervisar y validar operaciones'
        },
        {
            'name': 'Logística',
            'description': 'Responsable de asignación de logística y traslados'
        },
        {
            'name': 'Recepción',
            'description': 'Responsable de recepción en destino de traslados'
        },
        {
            'name': 'Conteo',
            'description': 'Responsable de realizar conteos físicos'
        },
        {
            'name': 'Gestor de Inventario',
            'description': 'Responsable de gestión general del inventario'
        },
        {
            'name': 'Administrador',
            'description': 'Administrador del sistema'
        },
    ]
    
    for role_data in roles:
        group, created = Group.objects.get_or_create(name=role_data['name'])
        if created:
            print(f"✅ Rol '{role_data['name']}' creado exitosamente")
        else:
            print(f"ℹ️  Rol '{role_data['name']}' ya existe")

def delete_roles(apps, schema_editor):
    """
    Elimina los roles creados (para revertir la migración)
    """
    roles = [
        'Revisión',
        'Almacenero',
        'Control Calidad',
        'Facturación',
        'Supervisión',
        'Logística',
        'Recepción',
        'Conteo',
        'Gestor de Inventario',
        'Administrador',
    ]
    
    for role_name in roles:
        try:
            group = Group.objects.get(name=role_name)
            group.delete()
            print(f"✅ Rol '{role_name}' eliminado")
        except Group.DoesNotExist:
            print(f"ℹ️  Rol '{role_name}' no encontrado")

class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0027_create_devolucion_tables'),
    ]

    operations = [
        migrations.RunPython(create_roles, delete_roles),
    ]
