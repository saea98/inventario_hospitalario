"""
Carga almacenes centrales nacionales desde el Excel de ratificación.

Uso:
  # Solo simular (recomendado primero)
  python manage.py cargar_almacenes_centrales "/ruta/al/archivo.xlsx" --dry-run

  # Aplicar en BD
  python manage.py cargar_almacenes_centrales "/ruta/al/archivo.xlsx" --aplicar
"""

from django.core.management.base import BaseCommand, CommandError

from inventario.almacenes_centrales_carga import (
    leer_filas_excel,
    procesar_almacenes_centrales,
)


class Command(BaseCommand):
    help = (
        'Carga almacenes centrales (Institucion + Almacen NAC-{CLUE}) '
        'desde el formato de actualización/ratificación. '
        'Por defecto solo dry-run.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            'ruta_excel',
            type=str,
            help='Ruta al archivo .xlsx',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simular sin escribir en BD (default si no se pasa --aplicar)',
        )
        parser.add_argument(
            '--aplicar',
            action='store_true',
            help='Escribir cambios en BD (requiere confirmación implícita al pasar la bandera)',
        )
        parser.add_argument(
            '--verbose-all',
            action='store_true',
            help='Mostrar también omisiones (sin cambios)',
        )

    def handle(self, *args, **options):
        ruta = options['ruta_excel']
        aplicar = options['aplicar']
        dry_run = not aplicar
        if options['dry_run'] and aplicar:
            raise CommandError('No combines --dry-run y --aplicar.')

        try:
            filas = leer_filas_excel(ruta)
        except Exception as e:
            raise CommandError(f'No se pudo leer el Excel: {e}') from e

        self.stdout.write(f'Filas leídas: {len(filas)}')
        modo = 'DRY-RUN (sin escribir)' if dry_run else 'APLICAR (escribe en BD)'
        self.stdout.write(self.style.WARNING(f'Modo: {modo}'))

        resultado = procesar_almacenes_centrales(filas, dry_run=dry_run)

        for accion in resultado.acciones:
            if accion.tipo.startswith('omitir') and not options['verbose_all']:
                continue
            estilo = self.style.ERROR if accion.tipo == 'error' else (
                self.style.SUCCESS if accion.tipo.startswith('crear') else self.style.NOTICE
            )
            self.stdout.write(estilo(f'[{accion.tipo}] {accion.mensaje}'))

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Resumen'))
        self.stdout.write(f'  Filas:                    {resultado.filas_leidas}')
        self.stdout.write(f'  Instituciones a crear:    {resultado.instituciones_crear}')
        self.stdout.write(f'  Instituciones a actualizar:{resultado.instituciones_actualizar}')
        self.stdout.write(f'  Almacenes a crear:        {resultado.almacenes_crear}')
        self.stdout.write(f'  Almacenes a actualizar:   {resultado.almacenes_actualizar}')
        self.stdout.write(f'  Omitidos (sin cambios):   {resultado.omitidos}')
        self.stdout.write(f'  Errores:                  {resultado.errores}')

        if dry_run:
            self.stdout.write('')
            self.stdout.write(
                self.style.WARNING(
                    'Dry-run terminado. Si el resumen es correcto, ejecuta de nuevo con --aplicar'
                )
            )
        elif resultado.errores:
            self.stdout.write(self.style.ERROR('Hubo errores; revisa el detalle arriba.'))
        else:
            self.stdout.write(self.style.SUCCESS('Carga aplicada correctamente.'))
