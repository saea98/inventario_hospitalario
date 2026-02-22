"""
Comando para limpiar LoteAsignado duplicados (mismo item_propuesta + lote_ubicacion).
Mantiene un registro por cada par (item_propuesta, lote_ubicacion) y elimina el resto.

Uso:
  python manage.py limpiar_lotes_asignados_duplicados           # aplicar cambios
  python manage.py limpiar_lotes_asignados_duplicados --dry-run # solo listar qué se haría
"""

from django.core.management.base import BaseCommand
from django.db.models import Count

from inventario.pedidos_models import LoteAsignado


class Command(BaseCommand):
    help = (
        'Elimina LoteAsignado duplicados: mismo item_propuesta y lote_ubicacion. '
        'Mantiene el registro más antiguo (por fecha_asignacion) y borra el resto.'
    )

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

        # Grupos (item_propuesta_id, lote_ubicacion_id) con más de un registro
        duplicados = (
            LoteAsignado.objects.values('item_propuesta_id', 'lote_ubicacion_id')
            .annotate(count=Count('id'))
            .filter(count__gt=1)
        )
        grupos = list(duplicados)
        if not grupos:
            self.stdout.write(self.style.SUCCESS('No hay LoteAsignado duplicados (mismo ítem + misma ubicación).'))
            return

        self.stdout.write(f'Se encontraron {len(grupos)} grupo(s) con duplicados.\n')
        eliminados = 0

        for g in grupos:
            item_id = g['item_propuesta_id']
            ubicacion_id = g['lote_ubicacion_id']
            qs = (
                LoteAsignado.objects.filter(
                    item_propuesta_id=item_id,
                    lote_ubicacion_id=ubicacion_id,
                )
                .select_related(
                    'item_propuesta__producto',
                    'lote_ubicacion__lote',
                    'lote_ubicacion__ubicacion',
                )
                .order_by('fecha_asignacion', 'id')
            )
            registros = list(qs)
            n = len(registros)
            mantener = registros[0]
            a_eliminar = registros[1:]

            # Info legible para el log
            producto = getattr(mantener.item_propuesta.producto, 'clave_cnis', '')
            lote = getattr(mantener.lote_ubicacion.lote, 'numero_lote', '')
            ubicacion = getattr(mantener.lote_ubicacion.ubicacion, 'codigo', '')
            self.stdout.write(
                f'  Item {item_id} / LoteUbicación {ubicacion_id}: '
                f'{producto} — lote {lote} @ {ubicacion} — {n} registro(s)'
            )

            if dry_run:
                self.stdout.write(self.style.WARNING(f'    (dry-run) Se eliminarían {len(a_eliminar)} duplicado(s).'))
            else:
                for la in a_eliminar:
                    la.delete()
                    eliminados += 1
                self.stdout.write(self.style.SUCCESS(f'    Eliminados {len(a_eliminar)} duplicado(s).'))

        if not dry_run and eliminados:
            self.stdout.write(self.style.SUCCESS(f'\n✅ Limpieza completada. Total eliminados: {eliminados}'))
        elif dry_run and grupos:
            self.stdout.write(self.style.WARNING('\nEjecuta sin --dry-run para aplicar los cambios.'))
