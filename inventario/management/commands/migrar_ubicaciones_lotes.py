"""
Comando para migrar las ubicaciones de los lotes existentes a la tabla LoteUbicacion.

Este comando busca todos los lotes que tengan almacen_id y ubicacion_id,
y crea registros en LoteUbicacion para cada uno.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from inventario.models import Lote, LoteUbicacion, UbicacionAlmacen


class Command(BaseCommand):
    help = 'Migra las ubicaciones de los lotes existentes a la tabla LoteUbicacion'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Muestra qué se haría sin hacer cambios reales',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        
        self.stdout.write(self.style.SUCCESS('Iniciando migración de ubicaciones de lotes...'))
        
        # Buscar todos los lotes que tengan almacen_id y ubicacion_id
        lotes = Lote.objects.filter(
            almacen_id__isnull=False,
            ubicacion_id__isnull=False
        )
        
        self.stdout.write(f'Se encontraron {lotes.count()} lotes con ubicación asignada')
        
        creados = 0
        duplicados = 0
        errores = 0
        
        for lote in lotes:
            try:
                # Verificar si ya existe un registro de LoteUbicacion para este lote
                existe = LoteUbicacion.objects.filter(
                    lote=lote,
                    ubicacion_id=lote.ubicacion_id
                ).exists()
                
                if existe:
                    self.stdout.write(
                        self.style.WARNING(
                            f'⚠️  Lote {lote.id} ya tiene ubicación {lote.ubicacion_id} registrada'
                        )
                    )
                    duplicados += 1
                    continue
                
                # Obtener la ubicación
                try:
                    ubicacion = UbicacionAlmacen.objects.get(id=lote.ubicacion_id)
                except UbicacionAlmacen.DoesNotExist:
                    self.stdout.write(
                        self.style.ERROR(
                            f'❌ Ubicación {lote.ubicacion_id} no existe para el lote {lote.id}'
                        )
                    )
                    errores += 1
                    continue
                
                # Crear el registro de LoteUbicacion
                if not dry_run:
                    LoteUbicacion.objects.create(
                        lote=lote,
                        ubicacion=ubicacion,
                        cantidad=lote.cantidad_disponible,
                        fecha_asignacion=timezone.now()
                    )
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Lote {lote.id}: Ubicación {ubicacion.codigo} ({ubicacion.id}) - '
                        f'Cantidad: {lote.cantidad_disponible}'
                    )
                )
                creados += 1
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Error al procesar lote {lote.id}: {str(e)}')
                )
                errores += 1
        
        # Resumen
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('RESUMEN DE LA MIGRACIÓN'))
        self.stdout.write('='*60)
        self.stdout.write(f'Registros creados: {creados}')
        self.stdout.write(f'Registros duplicados (ignorados): {duplicados}')
        self.stdout.write(f'Errores: {errores}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n⚠️  DRY RUN: No se realizaron cambios en la base de datos'))
        else:
            self.stdout.write(self.style.SUCCESS('\n✓ Migración completada exitosamente'))
