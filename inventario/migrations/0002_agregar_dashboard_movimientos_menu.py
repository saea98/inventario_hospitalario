# Generated migration to add Dashboard de Movimientos to menu

from django.db import migrations


def agregar_dashboard_menu(apps, schema_editor):
    """Agregar Dashboard de Movimientos al menú"""
    MenuItemRol = apps.get_model('inventario', 'MenuItemRol')
    Group = apps.get_model('auth', 'Group')
    
    # Obtener el menú padre "Reportes"
    try:
        reportes_menu = MenuItemRol.objects.get(menu_item='reportes_dashboard')
    except MenuItemRol.DoesNotExist:
        # Si no existe, crear el menú padre primero
        reportes_menu = MenuItemRol.objects.create(
            menu_item='reportes_dashboard',
            nombre_mostrado='Reportes',
            icono='fas fa-file-alt',
            url_name='reportes_dashboard',
            orden=5,
            activo=True,
            es_submenu=False,
        )
        # Asignar a todos los roles
        for role in Group.objects.all():
            reportes_menu.roles_permitidos.add(role)
    
    # Crear o actualizar el menú del Dashboard de Movimientos
    dashboard_movimientos, created = MenuItemRol.objects.get_or_create(
        menu_item='dashboard_movimientos',
        defaults={
            'nombre_mostrado': 'Dashboard de Movimientos',
            'icono': 'fas fa-chart-line',
            'url_name': 'dashboard_movimientos',
            'orden': 1,
            'activo': True,
            'es_submenu': True,
            'menu_padre': reportes_menu,
        }
    )
    
    if not created:
        # Actualizar si ya existe
        dashboard_movimientos.nombre_mostrado = 'Dashboard de Movimientos'
        dashboard_movimientos.icono = 'fas fa-chart-line'
        dashboard_movimientos.url_name = 'dashboard_movimientos'
        dashboard_movimientos.es_submenu = True
        dashboard_movimientos.menu_padre = reportes_menu
        dashboard_movimientos.save()
    
    # Asignar a todos los roles
    for role in Group.objects.all():
        dashboard_movimientos.roles_permitidos.add(role)


def revertir_dashboard_menu(apps, schema_editor):
    """Revertir cambios"""
    MenuItemRol = apps.get_model('inventario', 'MenuItemRol')
    try:
        dashboard = MenuItemRol.objects.get(menu_item='dashboard_movimientos')
        dashboard.delete()
    except MenuItemRol.DoesNotExist:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(agregar_dashboard_menu, revertir_dashboard_menu),
    ]
