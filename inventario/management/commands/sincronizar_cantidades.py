from django.core.management.base import BaseCommand
from django.db.models import Sum
from inventario.models import Lote, LoteUbicacion


class Command(BaseCommand):
    help = 'Sincroniza las cantidades de Lote con la suma de sus ubicaciones (LoteUbicacion)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--lote-id',
            type=int,
            help='ID específico de lote a sincronizar (opcional)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostrar cambios sin aplicarlos',
        )

    def handle(self, *args, **options):
        lote_id = options.get('lote_id')
        dry_run = options.get('dry_run', False)

        # Filtrar lotes
        if lote_id:
            lotes = Lote.objects.filter(id=lote_id)
            if not lotes.exists():
                self.stdout.write(self.style.ERROR(f'Lote con ID {lote_id} no encontrado'))
                return
        else:
            lotes = Lote.objects.all()

        self.stdout.write(f'Sincronizando {lotes.count()} lotes...\n')

        cambios = 0
        sin_cambios = 0

        for lote in lotes:
            # Calcular suma de ubicaciones
            cantidad_total = LoteUbicacion.objects.filter(lote=lote).aggregate(
                total=Sum('cantidad')
            )['total'] or 0

            # Comparar con cantidad actual
            if lote.cantidad_disponible != cantidad_total:
                cambios += 1
                mensaje = f'Lote {lote.numero_lote} ({lote.producto.clave_cnis}): '
                mensaje += f'{lote.cantidad_disponible} → {cantidad_total}'

                if dry_run:
                    self.stdout.write(self.style.WARNING(f'[DRY-RUN] {mensaje}'))
                else:
                    lote.cantidad_disponible = cantidad_total
                    lote.save(update_fields=['cantidad_disponible'])
                    self.stdout.write(self.style.SUCCESS(f'✓ {mensaje}'))
            else:
                sin_cambios += 1

        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS(f'Cambios realizados: {cambios}'))
        self.stdout.write(f'Sin cambios: {sin_cambios}')
        if dry_run:
            self.stdout.write(self.style.WARNING('(Modo DRY-RUN - no se aplicaron cambios)'))
