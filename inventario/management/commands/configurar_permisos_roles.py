"""
Comando de Django para configurar permisos específicos por rol
Asigna permisos de Django a los grupos según el Manual de Procedimientos
Uso: python manage.py configurar_permisos_roles
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType


class Command(BaseCommand):
    help = 'Configura permisos específicos para cada rol del sistema'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n' + '='*70))
        self.stdout.write(self.style.SUCCESS('🔐 CONFIGURAR PERMISOS POR ROLES'))
        self.stdout.write(self.style.SUCCESS('='*70 + '\n'))

        # Definir permisos por rol
        permisos_por_rol = {
            'Administrador': [
                # Todos los permisos
                'inventario.add_user',
                'inventario.change_user',
                'inventario.delete_user',
                'inventario.view_user',
                'inventario.add_almacen',
                'inventario.change_almacen',
                'inventario.delete_almacen',
                'inventario.view_almacen',
                'inventario.add_lote',
                'inventario.change_lote',
                'inventario.delete_lote',
                'inventario.view_lote',
                'inventario.add_menuitemrol',
                'inventario.change_menuitemrol',
                'inventario.delete_menuitemrol',
                'inventario.view_menuitemrol',
                'auth.add_group',
                'auth.change_group',
                'auth.delete_group',
                'auth.view_group',
            ],
            
            'Almacenero': [
                # Gestión de lotes y existencias
                'inventario.view_lote',
                'inventario.add_lote',
                'inventario.change_lote',
                # Entrada al almacén
                'inventario.add_entradaalmacen',
                'inventario.change_entradaalmacen',
                'inventario.view_entradaalmacen',
                # Picking
                'inventario.view_propuestapedido',
                'inventario.change_propuestapedido',
                # Devoluciones
                'inventario.view_devolucion',
                'inventario.add_devolucion',
            ],
            
            'Supervisión': [
                # Ver todo
                'inventario.view_lote',
                'inventario.view_entradaalmacen',
                'inventario.view_propuestapedido',
                'inventario.view_solicitudpedido',
                'inventario.view_devolucion',
                'inventario.view_movimientoinventario',
                # Cambiar estados
                'inventario.change_propuestapedido',
                'inventario.change_solicitudpedido',
                'inventario.change_devolucion',
            ],
            
            'Control Calidad': [
                # Inspeccionar productos
                'inventario.view_lote',
                'inventario.change_lote',
                'inventario.view_entradaalmacen',
                'inventario.change_entradaalmacen',
            ],
            
            'Facturación': [
                # Gestionar facturas
                'inventario.view_lote',
                'inventario.view_propuestapedido',
                'inventario.view_solicitudpedido',
                'inventario.view_movimientoinventario',
            ],
            
            'Revisión': [
                # Revisar citas y pedidos
                'inventario.view_solicitudpedido',
                'inventario.change_solicitudpedido',
                'inventario.view_propuestapedido',
            ],
            
            'Logística': [
                # Gestionar traslados
                'inventario.view_lote',
                'inventario.view_propuestapedido',
                'inventario.view_solicitudpedido',
                'inventario.view_movimientoinventario',
            ],
            
            'Recepción': [
                # Recepción en destino
                'inventario.view_lote',
                'inventario.change_lote',
                'inventario.view_propuestapedido',
                'inventario.change_propuestapedido',
            ],
            
            'Conteo': [
                # Conteo físico
                'inventario.view_lote',
                'inventario.change_lote',
                'inventario.view_movimientoinventario',
                'inventario.add_movimientoinventario',
            ],
            
            'Gestor de Inventario': [
                # Gestión general
                'inventario.view_lote',
                'inventario.change_lote',
                'inventario.view_movimientoinventario',
                'inventario.add_movimientoinventario',
                'inventario.change_movimientoinventario',
                'inventario.view_propuestapedido',
                'inventario.view_solicitudpedido',
            ],
        }

        # Aplicar permisos a cada rol
        for rol_nombre, permisos_list in permisos_por_rol.items():
            try:
                rol = Group.objects.get(name=rol_nombre)
                
                # Limpiar permisos actuales
                rol.permissions.clear()
                
                # Agregar nuevos permisos
                permisos_agregados = 0
                for permiso_codename in permisos_list:
                    try:
                        # Obtener el permiso
                        if '.' in permiso_codename:
                            app_label, codename = permiso_codename.split('.')
                        else:
                            app_label = 'inventario'
                            codename = permiso_codename
                        
                        permiso = Permission.objects.get(
                            content_type__app_label=app_label,
                            codename=codename
                        )
                        rol.permissions.add(permiso)
                        permisos_agregados += 1
                    except Permission.DoesNotExist:
                        self.stdout.write(
                            self.style.WARNING(f'⚠️  Permiso no encontrado: {permiso_codename}')
                        )
                
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Rol "{rol_nombre}": {permisos_agregados} permiso(s) asignado(s)')
                )
            
            except Group.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'❌ Rol "{rol_nombre}" no encontrado')
                )

        self.stdout.write(self.style.SUCCESS('\n' + '='*70))
        self.stdout.write(self.style.SUCCESS('✨ Configuración de permisos completada'))
        self.stdout.write(self.style.SUCCESS('='*70 + '\n'))
