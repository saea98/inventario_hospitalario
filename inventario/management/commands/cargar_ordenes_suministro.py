"""
Comando para carga masiva de órdenes de suministro desde Excel.

Crea registros en inventario_ordensuministro y vincula lotes existentes
mediante numero_lote + producto_id (clave_cnis).

Columnas esperadas en Excel:
- CLUES: Código de institución (para buscar Lote)
- ORDEN DE SUMINISTRO: Número de orden
- RFC: RFC del proveedor
- CLAVE: Clave CNIS del producto
- LOTE: Número de lote
- F_REC: Fecha de recepción (para fecha_orden)
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from datetime import datetime, date
import pandas as pd

from inventario.models import (
    OrdenSuministro, Lote, Producto, Proveedor, Institucion
)


def _procesar_fecha(valor):
    """Convierte valor a date."""
    if pd.isna(valor) or valor == '':
        return None
    try:
        if hasattr(valor, 'date'):
            return valor.date()
        if isinstance(valor, date):
            return valor
        if isinstance(valor, str):
            for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y']:
                try:
                    return datetime.strptime(valor.strip(), fmt).date()
                except ValueError:
                    continue
        return pd.to_datetime(valor).date()
    except Exception:
        return None


class Command(BaseCommand):
    help = 'Carga masiva de órdenes de suministro desde Excel y vincula lotes existentes'

    def add_arguments(self, parser):
        parser.add_argument(
            'archivo',
            type=str,
            help='Ruta del archivo Excel a procesar',
        )
        parser.add_argument(
            '--partida-default',
            type=str,
            default='N/A',
            help='Partida presupuestal por defecto si no se encuentra en producto (max 20 chars)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostrar cambios sin aplicarlos',
        )

    def handle(self, *args, **options):
        archivo = options['archivo']
        partida_default = str(options['partida_default'])[:20]
        dry_run = options.get('dry_run', False)

        self.stdout.write(f'📁 Leyendo archivo: {archivo}')

        try:
            df = pd.read_excel(archivo)
        except FileNotFoundError:
            raise CommandError(f'Archivo no encontrado: {archivo}')
        except Exception as e:
            raise CommandError(f'Error al leer archivo: {str(e)}')

        # Validar columnas requeridas
        columnas_requeridas = ['ORDEN DE SUMINISTRO', 'RFC', 'CLAVE', 'LOTE']
        columnas_opcionales = ['CLUES', 'F_REC']
        columnas_excel = [c.strip() for c in df.columns]

        faltantes = [c for c in columnas_requeridas if c not in columnas_excel]
        if faltantes:
            raise CommandError(
                f'Columnas requeridas faltantes: {faltantes}. '
                f'Columnas encontradas: {list(df.columns)}'
            )

        # CLUES es requerido para buscar Lote por institución
        if 'CLUES' not in columnas_excel:
            raise CommandError('La columna CLUES es requerida para vincular lotes por institución')

        self.stdout.write(f'📊 Total de registros: {len(df)}')

        stats = {
            'ordenes_creadas': 0,
            'ordenes_existentes': 0,
            'lotes_vinculados': 0,
            'lotes_no_encontrados': 0,
            'productos_no_encontrados': 0,
            'instituciones_no_encontradas': 0,
            'omitidos': 0,
            'errores': 0,
            'errores_detalle': [],
        }

        # Cache para órdenes ya creadas en esta ejecución
        cache_ordenes = {}

        if not dry_run:
            transaction.set_autocommit(False)

        try:
            for idx, row in df.iterrows():
                try:
                    clave = str(row.get('CLAVE', '')).strip()
                    if clave in ('S/CLAVE', 'nan', ''):
                        stats['omitidos'] += 1
                        continue

                    orden_numero = str(row.get('ORDEN DE SUMINISTRO', '')).strip()[:200]
                    rfc = str(row.get('RFC', '')).strip()[:13]
                    lote_numero = str(row.get('LOTE', '')).strip()[:50]
                    clues = str(row.get('CLUES', '')).strip()

                    if not orden_numero or not rfc or not lote_numero or not clues:
                        stats['errores'] += 1
                        stats['errores_detalle'].append(
                            f"Fila {idx+2}: Datos incompletos (ORDEN, RFC, LOTE o CLUES vacíos)"
                        )
                        continue

                    # 1. Buscar o crear Proveedor
                    try:
                        proveedor = Proveedor.objects.get(rfc=rfc)
                    except Proveedor.DoesNotExist:
                        proveedor = Proveedor.objects.create(
                            rfc=rfc,
                            razon_social=f'Proveedor {rfc}',
                            activo=True,
                        )

                    # 2. Buscar Producto (para partida_presupuestal)
                    try:
                        producto = Producto.objects.get(clave_cnis=clave)
                        partida = (producto.partida_presupuestal or partida_default)[:20]
                    except Producto.DoesNotExist:
                        stats['productos_no_encontrados'] += 1
                        stats['errores_detalle'].append(
                            f"Fila {idx+2}: Producto con CLAVE '{clave}' no existe"
                        )
                        continue

                    # 3. Buscar Institución
                    try:
                        institucion = Institucion.objects.get(clue=clues)
                    except Institucion.DoesNotExist:
                        stats['instituciones_no_encontradas'] += 1
                        stats['errores_detalle'].append(
                            f"Fila {idx+2}: Institución con CLUES '{clues}' no existe"
                        )
                        continue

                    # 4. Crear o obtener OrdenSuministro
                    cache_key = orden_numero
                    if cache_key in cache_ordenes:
                        orden = cache_ordenes[cache_key]
                    else:
                        f_rec = _procesar_fecha(row.get('F_REC'))
                        fecha_orden = f_rec or timezone.now().date()

                        orden, creada = OrdenSuministro.objects.get_or_create(
                            numero_orden=orden_numero,
                            defaults={
                                'proveedor': proveedor,
                                'partida_presupuestal': partida,
                                'fecha_orden': fecha_orden,
                                'activo': True,
                            }
                        )
                        cache_ordenes[cache_key] = orden
                        if creada:
                            stats['ordenes_creadas'] += 1
                        else:
                            stats['ordenes_existentes'] += 1

                    # 5. Buscar Lote y vincular
                    try:
                        lote = Lote.objects.get(
                            numero_lote=lote_numero,
                            producto=producto,
                            institucion=institucion,
                        )
                        if lote.orden_suministro_id != orden.id:
                            if not dry_run:
                                lote.orden_suministro = orden
                                lote.save()
                            stats['lotes_vinculados'] += 1
                    except Lote.DoesNotExist:
                        stats['lotes_no_encontrados'] += 1
                        stats['errores_detalle'].append(
                            f"Fila {idx+2}: Lote no encontrado (LOTE={lote_numero}, CLAVE={clave}, CLUES={clues})"
                        )
                    except Lote.MultipleObjectsReturned:
                        # Tomar el primero y actualizar
                        lote = Lote.objects.filter(
                            numero_lote=lote_numero,
                            producto=producto,
                            institucion=institucion,
                        ).first()
                        if not dry_run and lote.orden_suministro_id != orden.id:
                            lote.orden_suministro = orden
                            lote.save()
                        stats['lotes_vinculados'] += 1

                except Exception as e:
                    stats['errores'] += 1
                    stats['errores_detalle'].append(f"Fila {idx+2}: {str(e)}")

            if not dry_run:
                transaction.commit()
        except Exception as e:
            if not dry_run:
                transaction.rollback()
            raise CommandError(str(e))
        finally:
            if not dry_run:
                transaction.set_autocommit(True)

        # Resumen
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write(self.style.SUCCESS('✅ RESUMEN CARGA ÓRDENES DE SUMINISTRO'))
        self.stdout.write('=' * 70)
        self.stdout.write(f"📦 Órdenes creadas: {stats['ordenes_creadas']}")
        self.stdout.write(f"📋 Órdenes ya existentes: {stats['ordenes_existentes']}")
        self.stdout.write(f"🔗 Lotes vinculados: {stats['lotes_vinculados']}")
        self.stdout.write(f"⏭️  Omitidos (S/CLAVE): {stats['omitidos']}")
        self.stdout.write(self.style.WARNING(
            f"⚠️  Lotes no encontrados: {stats['lotes_no_encontrados']}"
        ))
        self.stdout.write(self.style.WARNING(
            f"⚠️  Productos no encontrados: {stats['productos_no_encontrados']}"
        ))
        self.stdout.write(self.style.WARNING(
            f"⚠️  Instituciones no encontradas: {stats['instituciones_no_encontradas']}"
        ))
        self.stdout.write(self.style.ERROR(f"❌ Errores: {stats['errores']}"))

        if stats['errores_detalle']:
            self.stdout.write('\n' + self.style.ERROR('ERRORES DETALLADOS (primeros 15):'))
            for err in stats['errores_detalle'][:15]:
                self.stdout.write(f"  - {err}")
            if len(stats['errores_detalle']) > 15:
                self.stdout.write(f"  ... y {len(stats['errores_detalle']) - 15} más")

        if dry_run:
            self.stdout.write(self.style.WARNING('\n⚠️  MODO DRY-RUN - Cambios NO aplicados'))
        else:
            self.stdout.write(self.style.SUCCESS('\n✅ Carga completada'))
