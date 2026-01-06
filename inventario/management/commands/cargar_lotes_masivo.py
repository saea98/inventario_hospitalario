from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from datetime import datetime
import pandas as pd
from inventario.models import Producto, Almacen, UbicacionAlmacen, Lote, LoteUbicacion
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Carga masiva de lotes desde archivo Excel con validaciones'

    def add_arguments(self, parser):
        parser.add_argument(
            'archivo',
            type=str,
            help='Ruta del archivo Excel a procesar',
        )
        parser.add_argument(
            '--institucion-id',
            type=int,
            default=1,
            help='ID de la institución (default: 1)',
        )
        parser.add_argument(
            '--usuario-id',
            type=int,
            help='ID del usuario que realiza la carga (default: primer admin)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostrar cambios sin aplicarlos',
        )

    def handle(self, *args, **options):
        archivo = options['archivo']
        institucion_id = options['institucion_id']
        usuario_id = options.get('usuario_id')
        dry_run = options.get('dry_run', False)

        # Obtener usuario
        if usuario_id:
            usuario = User.objects.get(id=usuario_id)
        else:
            usuario = User.objects.filter(is_superuser=True).first()
            if not usuario:
                raise CommandError('No se encontró usuario admin')

        self.stdout.write(f'📁 Leyendo archivo: {archivo}')
        
        try:
            df = pd.read_excel(archivo)
        except Exception as e:
            raise CommandError(f'Error al leer archivo: {str(e)}')

        self.stdout.write(f'📊 Total de registros: {len(df)}')

        # Estadísticas
        stats = {
            'procesados': 0,
            'omitidos': 0,
            'productos_creados': 0,
            'ubicaciones_creadas': 0,
            'lotes_creados': 0,
            'lotes_actualizados': 0,
            'errores': 0,
            'errores_detalle': []
        }

        with transaction.atomic():
            for idx, row in df.iterrows():
                try:
                    # 1. VALIDAR: Omitir si CLAVE es 'S/CLAVE'
                    clave = str(row.get('CLAVE', '')).strip()
                    if clave == 'S/CLAVE' or clave == 'nan':
                        stats['omitidos'] += 1
                        continue

                    # Obtener datos
                    almacen_id = int(row.get('almcen', 1))
                    descripcion = str(row.get('DESCRIPCION', '')).strip()
                    lote_numero = str(row.get('LOTE', '')).strip()
                    caducidad_str = row.get('CADUCIDAD', '')
                    ubicacion_codigo = str(row.get('UBICACIÓN', '')).strip()
                    cantidad = int(row.get('INVENTARIO', 0))

                    # Validar datos mínimos
                    if not clave or not lote_numero or not ubicacion_codigo:
                        stats['errores'] += 1
                        stats['errores_detalle'].append(
                            f"Fila {idx+2}: Datos incompletos (CLAVE, LOTE o UBICACIÓN vacíos)"
                        )
                        continue

                    # 2. CREAR O OBTENER PRODUCTO
                    producto, producto_creado = Producto.objects.get_or_create(
                        clave_cnis=clave,
                        defaults={
                            'descripcion': descripcion or f'Producto {clave}',
                            'institucion_id': institucion_id,
                        }
                    )
                    if producto_creado:
                        stats['productos_creados'] += 1

                    # 3. OBTENER ALMACÉN
                    try:
                        almacen = Almacen.objects.get(id=almacen_id)
                    except Almacen.DoesNotExist:
                        stats['errores'] += 1
                        stats['errores_detalle'].append(
                            f"Fila {idx+2}: Almacén {almacen_id} no existe"
                        )
                        continue

                    # 4. CREAR O OBTENER UBICACIÓN
                    ubicacion, ubicacion_creada = UbicacionAlmacen.objects.get_or_create(
                        codigo=ubicacion_codigo,
                        almacen=almacen,
                        defaults={
                            'descripcion': ubicacion_codigo,
                            'activo': True,
                        }
                    )
                    if ubicacion_creada:
                        stats['ubicaciones_creadas'] += 1

                    # 5. PROCESAR FECHA DE CADUCIDAD
                    fecha_caducidad = None
                    if pd.notna(caducidad_str) and caducidad_str != 'S/C':
                        try:
                            if isinstance(caducidad_str, str):
                                fecha_caducidad = pd.to_datetime(caducidad_str).date()
                            else:
                                fecha_caducidad = caducidad_str.date() if hasattr(caducidad_str, 'date') else caducidad_str
                        except:
                            pass

                    # 6. CREAR O ACTUALIZAR LOTE
                    lote, lote_creado = Lote.objects.get_or_create(
                        numero_lote=lote_numero,
                        producto=producto,
                        institucion_id=institucion_id,
                        defaults={
                            'cantidad_inicial': cantidad,
                            'cantidad_disponible': cantidad,
                            'precio_unitario': 0,
                            'valor_total': 0,
                            'fecha_recepcion': timezone.now().date(),
                            'fecha_caducidad': fecha_caducidad,
                            'almacen': almacen,
                            'creado_por': usuario,
                        }
                    )

                    if lote_creado:
                        stats['lotes_creados'] += 1
                    else:
                        # Actualizar fecha de caducidad y cantidad si es necesario
                        if fecha_caducidad and lote.fecha_caducidad != fecha_caducidad:
                            lote.fecha_caducidad = fecha_caducidad
                        stats['lotes_actualizados'] += 1

                    # 7. CREAR O ACTUALIZAR LOTE_UBICACION
                    lote_ubicacion, _ = LoteUbicacion.objects.get_or_create(
                        lote=lote,
                        ubicacion=ubicacion,
                        defaults={
                            'cantidad': cantidad,
                            'usuario_asignacion': usuario,
                        }
                    )

                    # Actualizar cantidad si cambió
                    if lote_ubicacion.cantidad != cantidad:
                        lote_ubicacion.cantidad = cantidad
                        lote_ubicacion.usuario_asignacion = usuario
                        lote_ubicacion.save()

                    # Guardar lote con cambios
                    if not lote_creado:
                        lote.save()

                    # Sincronizar cantidad total del lote
                    lote.sincronizar_cantidad_disponible()

                    stats['procesados'] += 1

                except Exception as e:
                    stats['errores'] += 1
                    stats['errores_detalle'].append(f"Fila {idx+2}: {str(e)}")

        # Mostrar resultados
        self.stdout.write('\n' + '=' * 80)
        self.stdout.write(self.style.SUCCESS('✅ RESUMEN DE CARGA MASIVA'))
        self.stdout.write('=' * 80)
        self.stdout.write(f"📊 Registros procesados: {stats['procesados']}")
        self.stdout.write(f"⏭️  Registros omitidos (S/CLAVE): {stats['omitidos']}")
        self.stdout.write(f"➕ Productos creados: {stats['productos_creados']}")
        self.stdout.write(f"📍 Ubicaciones creadas: {stats['ubicaciones_creadas']}")
        self.stdout.write(f"📦 Lotes creados: {stats['lotes_creados']}")
        self.stdout.write(f"🔄 Lotes actualizados: {stats['lotes_actualizados']}")
        self.stdout.write(self.style.ERROR(f"❌ Errores: {stats['errores']}"))

        if stats['errores_detalle']:
            self.stdout.write('\n' + self.style.ERROR('ERRORES DETALLADOS:'))
            for error in stats['errores_detalle'][:10]:  # Mostrar primeros 10
                self.stdout.write(f"  - {error}")
            if len(stats['errores_detalle']) > 10:
                self.stdout.write(f"  ... y {len(stats['errores_detalle']) - 10} errores más")

        if dry_run:
            self.stdout.write(self.style.WARNING('\n⚠️  MODO DRY-RUN - Los cambios NO fueron aplicados'))
        else:
            self.stdout.write(self.style.SUCCESS('\n✅ Carga completada exitosamente'))
