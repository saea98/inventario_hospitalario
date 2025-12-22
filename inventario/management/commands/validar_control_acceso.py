"""
Comando para validar que el control de acceso esté sincronizado
Verifica que MenuItemRol coincida con los decoradores en las vistas
"""

from django.core.management.base import BaseCommand
from django.urls import get_resolver
from inventario.models import MenuItemRol
import inspect
import re


class Command(BaseCommand):
    help = 'Valida que MenuItemRol esté sincronizado con los decoradores de las vistas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Mostrar información detallada'
        )
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Intentar corregir desajustes automáticamente'
        )

    def handle(self, *args, **options):
        verbose = options['verbose']
        fix = options['fix']

        self.stdout.write(self.style.SUCCESS('\n' + '='*80))
        self.stdout.write(self.style.SUCCESS('VALIDACIÓN DE CONTROL DE ACCESO'))
        self.stdout.write(self.style.SUCCESS('='*80 + '\n'))

        # Obtener todas las URLs y sus vistas
        resolver = get_resolver()
        url_patterns = self._get_all_url_patterns(resolver)

        desajustes = []
        items_sin_decorador = []
        items_sin_menuitemrol = []

        # Verificar cada patrón de URL
        for url_name, view_func in url_patterns:
            # Obtener decoradores de la vista
            decoradores = self._obtener_decoradores(view_func)

            # Obtener configuración de MenuItemRol
            try:
                menu_item = MenuItemRol.objects.get(url_name=url_name, activo=True)
                roles_menuitem = set(menu_item.roles_permitidos.values_list('name', flat=True))

                # Comparar
                if decoradores and decoradores != roles_menuitem:
                    desajustes.append({
                        'url_name': url_name,
                        'decorador': decoradores,
                        'menuitem': roles_menuitem,
                        'menu_nombre': menu_item.nombre_mostrado
                    })

                if verbose:
                    self.stdout.write(f"✅ {url_name}: MenuItemRol={roles_menuitem}")

            except MenuItemRol.DoesNotExist:
                if decoradores:
                    items_sin_menuitemrol.append({
                        'url_name': url_name,
                        'decorador': decoradores
                    })
                    if verbose:
                        self.stdout.write(
                            self.style.WARNING(f"⚠️  {url_name}: Tiene decorador pero NO está en MenuItemRol")
                        )

        # Mostrar desajustes
        if desajustes:
            self.stdout.write(self.style.ERROR('\n❌ DESAJUSTES ENCONTRADOS:\n'))
            for desajuste in desajustes:
                self.stdout.write(
                    self.style.ERROR(
                        f"  • {desajuste['url_name']} ({desajuste['menu_nombre']})\n"
                        f"    Decorador: {desajuste['decorador']}\n"
                        f"    MenuItemRol: {desajuste['menuitem']}\n"
                    )
                )
        else:
            self.stdout.write(self.style.SUCCESS('✅ No hay desajustes entre decoradores y MenuItemRol\n'))

        # Mostrar items sin MenuItemRol
        if items_sin_menuitemrol:
            self.stdout.write(self.style.WARNING('\n⚠️  VISTAS CON DECORADOR PERO SIN MenuItemRol:\n'))
            for item in items_sin_menuitemrol:
                self.stdout.write(
                    self.style.WARNING(
                        f"  • {item['url_name']}\n"
                        f"    Decorador: {item['decorador']}\n"
                    )
                )

        # Resumen
        self.stdout.write(self.style.SUCCESS('\n' + '='*80))
        self.stdout.write(self.style.SUCCESS('RESUMEN'))
        self.stdout.write(self.style.SUCCESS('='*80))
        self.stdout.write(self.style.SUCCESS(f"Total de URLs: {len(url_patterns)}"))
        self.stdout.write(self.style.SUCCESS(f"Desajustes: {len(desajustes)}"))
        self.stdout.write(self.style.SUCCESS(f"Vistas sin MenuItemRol: {len(items_sin_menuitemrol)}"))
        self.stdout.write(self.style.SUCCESS('='*80 + '\n'))

        if desajustes or items_sin_menuitemrol:
            return 1
        return 0

    def _get_all_url_patterns(self, resolver, prefix=''):
        """
        Obtiene todos los patrones de URL del proyecto
        """
        patterns = []

        for pattern in resolver.url_patterns:
            if hasattr(pattern, 'url_patterns'):
                # Es un include()
                new_prefix = prefix + str(pattern.pattern)
                patterns.extend(self._get_all_url_patterns(pattern, new_prefix))
            else:
                # Es una URL normal
                url_name = pattern.name
                if url_name:
                    try:
                        view_func = pattern.callback
                        patterns.append((url_name, view_func))
                    except:
                        pass

        return patterns

    def _obtener_decoradores(self, view_func):
        """
        Obtiene los roles especificados en los decoradores @requiere_rol
        """
        roles = set()

        # Obtener el código fuente de la vista
        try:
            source = inspect.getsource(view_func)

            # Buscar decoradores @requiere_rol
            patron = r"@requiere_rol\(['\"]([^'\"]+)['\"]\)"
            matches = re.findall(patron, source)

            for match in matches:
                roles.add(match.strip())

            # Buscar decoradores con múltiples roles
            patron_multi = r"@requiere_rol\(([^)]+)\)"
            matches_multi = re.findall(patron_multi, source)

            for match in matches_multi:
                # Extraer los roles entre comillas
                roles_match = re.findall(r"['\"]([^'\"]+)['\"]", match)
                for rol in roles_match:
                    roles.add(rol.strip())

        except:
            pass

        return roles
