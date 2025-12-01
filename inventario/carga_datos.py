# inventario/carga_datos.py
import pandas as pd
from django.db import transaction
from .models import Lote, UbicacionAlmacen, Institucion, Producto, Almacen, CategoriaProducto

def carga_lotes_desde_excel(archivo_excel, institucion_id, usuario=None):
    """
    Carga lotes desde archivo Excel y los asocia con ubicaciones existentes
    La columna UBICACIÓN del Excel corresponde al campo descripcion del modelo
    """
    try:
        # Leer el archivo Excel
        df = pd.read_excel(archivo_excel)
        
        print(f"📊 Se encontraron {len(df)} registros en el archivo")
        print("⏳ Procesando...")
        
        # Contadores para estadísticas
        exitosos = 0
        errores = 0
        actualizados = 0
        ubicaciones_no_encontradas = set()
        
        # Obtener la institución
        try:
            institucion = Institucion.objects.get(id=institucion_id)
        except Institucion.DoesNotExist:
            return {
                'success': False,
                'message': f"❌ Institución con ID {institucion_id} no encontrada"
            }
        
        with transaction.atomic():
            for index, row in df.iterrows():
                try:
                    numero_lote = str(row['LOTE']).strip()
                    ubicacion_descripcion = str(row['UBICACIÓN']).strip()
                    
                    # Buscar la ubicación por DESCRIPCION (no por código)
                    ubicacion_db = UbicacionAlmacen.objects.filter(
                        descripcion=ubicacion_descripcion
                    ).first()
                    
                    if ubicacion_db:
                        # Verificar si el lote ya existe
                        lote_existente = Lote.objects.filter(
                            numero_lote=numero_lote,
                            institucion=institucion
                        ).first()
                        
                        if lote_existente:
                            # Actualizar lote existente
                            lote_existente.ubicacion = ubicacion_db
                            lote_existente.almacen = ubicacion_db.almacen
                            lote_existente.save()
                            actualizados += 1
                            print(f"✅ Lote actualizado: {numero_lote} -> {ubicacion_descripcion}")
                        else:
                            # Crear un lote básico (requiere campos obligatorios)
                            # Buscar un producto por defecto o crear uno
                            producto_default = Producto.objects.first()
                            if not producto_default:
                                # Crear un producto por defecto si no existe
                                categoria_default, _ = CategoriaProducto.objects.get_or_create(
                                    nombre='DEFAULT',
                                    defaults={'descripcion': 'Categoría por defecto'}
                                )
                                producto_default = Producto.objects.create(
                                    clave_cnis='PRODUCTO_DEFAULT',
                                    descripcion='Producto por defecto para carga de lotes',
                                    categoria=categoria_default,
                                    unidad_medida='PIEZA',
                                    activo=True
                                )
                            
                            nuevo_lote = Lote(
                                numero_lote=numero_lote,
                                institucion=institucion,
                                almacen=ubicacion_db.almacen,
                                ubicacion=ubicacion_db,
                                producto=producto_default,
                                cantidad_inicial=0,
                                cantidad_disponible=0,
                                precio_unitario=0,
                                valor_total=0,
                                fecha_recepcion=pd.Timestamp.now().date(),
                                estado=1,  # Disponible
                                creado_por=usuario
                            )
                            nuevo_lote.save()
                            exitosos += 1
                            print(f"✅ Lote creado: {numero_lote} -> {ubicacion_descripcion}")
                        
                    else:
                        ubicaciones_no_encontradas.add(ubicacion_descripcion)
                        errores += 1
                        print(f"❌ Ubicación no encontrada: {ubicacion_descripcion} para lote {numero_lote}")
                        
                except Exception as e:
                    errores += 1
                    print(f"❌ Error procesando fila {index + 1}: {e}")
                    continue
        
        # Preparar resultado
        resultado = {
            'success': True,
            'exitosos': exitosos,
            'actualizados': actualizados,
            'errores': errores,
            'ubicaciones_no_encontradas': list(ubicaciones_no_encontradas)
        }
        
        # Mostrar resumen
        print(f"\n🎯 RESUMEN DE CARGA")
        print(f"✅ Lotes creados: {exitosos}")
        print(f"🔄 Lotes actualizados: {actualizados}")
        print(f"❌ Errores: {errores}")
        
        if ubicaciones_no_encontradas:
            print(f"\n⚠️ Ubicaciones no encontradas ({len(ubicaciones_no_encontradas)} únicas):")
            for ubicacion in sorted(list(ubicaciones_no_encontradas))[:10]:
                print(f"  - {ubicacion}")
            if len(ubicaciones_no_encontradas) > 10:
                print(f"  ... y {len(ubicaciones_no_encontradas) - 10} más")
                
        return resultado
                
    except FileNotFoundError:
        return {
            'success': False,
            'message': f"❌ Error: No se encontró el archivo {archivo_excel}"
        }
    except Exception as e:
        return {
            'success': False,
            'message': f"❌ Error inesperado: {e}"
        }