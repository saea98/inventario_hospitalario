"""
Comando para limpiar MenuItemRol duplicados por url_name.
Uso (también dentro de contenedor Docker):
  python manage.py limpiar_menu_duplicados
"""

from django.core.management.base import BaseCommand
from django.db.models import Count

from inventario.models import MenuItemRol


class Command(BaseCommand):
    help = 'Elimina registros duplicados de MenuItemRol (mantiene uno por url_name).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Solo mostrar qué se eliminaría, sin borrar.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        if dry_run:
            self.stdout.write(self.style.WARNING('Modo dry-run: no se eliminará nada.\n'))

        duplicados = (
            MenuItemRol.objects.values('url_name')
            .annotate(count=Count('id'))
            .filter(count__gt=1)
        )
        total = list(duplicados)
        if not total:
            self.stdout.write(self.style.SUCCESS('No hay MenuItemRol duplicados por url_name.'))
            return

        self.stdout.write(f'Se encontraron {len(total)} url_name con duplicados.\n')

        eliminados = 0
        for dup in total:
            url_name = dup['url_name']
            items = MenuItemRol.objects.filter(url_name=url_name).order_by('id')
            count = items.count()
            self.stdout.write(f'  url_name: {url_name} — {count} registro(s)')

            if count > 1:
                primer_item = items.first()
                items_a_eliminar = items.exclude(id=primer_item.id)
                n = items_a_eliminar.count()
                if dry_run:
                    self.stdout.write(self.style.WARNING(f'    (dry-run) Se eliminarían {n} duplicado(s).'))
                else:
                    items_a_eliminar.delete()
                    eliminados += n
                    self.stdout.write(self.style.SUCCESS(f'    Eliminados {n} duplicado(s).'))

        if not dry_run and eliminados:
            self.stdout.write(self.style.SUCCESS(f'\n✅ Limpieza completada. Total eliminados: {eliminados}'))
        elif dry_run and total:
            self.stdout.write(self.style.WARNING('\nEjecuta sin --dry-run para aplicar los cambios.'))
