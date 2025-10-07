from django.http import HttpResponse
from django.template.loader import get_template
from django.db.models import Sum, Count, Q
from datetime import date, timedelta
import pandas as pd
from io import BytesIO
from .models import Lote, Institucion, Producto, MovimientoInventario


class ReportGenerator:
    """Generador de reportes para el sistema de inventario"""
    
    def generar_reporte_inventario_excel(self, filtros=None):
        """Genera reporte de inventario en formato Excel"""
        
        # Obtener datos base
        lotes = Lote.objects.select_related(
            'producto', 'institucion', 'orden_suministro__proveedor'
        ).filter(estado=1)  # Solo lotes disponibles
        
        # Aplicar filtros si existen
        if filtros:
            if filtros.get('institucion'):
                lotes = lotes.filter(institucion=filtros['institucion'])
            if filtros.get('categoria'):
                lotes = lotes.filter(producto__categoria=filtros['categoria'])
            if filtros.get('fecha_desde'):
                lotes = lotes.filter(fecha_caducidad__gte=filtros['fecha_desde'])
            if filtros.get('fecha_hasta'):
                lotes = lotes.filter(fecha_caducidad__lte=filtros['fecha_hasta'])
        
        # Preparar datos para Excel
        data = []
        for lote in lotes:
            data.append({
                'CLUE': lote.institucion.clue,
                'Institución': lote.institucion.denominacion,
                'Alcaldía': lote.institucion.alcaldia.nombre,
                'Clave/CNIS': lote.producto.clave_cnis,
                'Descripción': lote.producto.descripcion,
                'Categoría': lote.producto.categoria.nombre,
                'Número de Lote': lote.numero_lote,
                'Cantidad Disponible': lote.cantidad_disponible,
                'Precio Unitario': float(lote.precio_unitario),
                'Valor Total': float(lote.valor_total),
                'Fecha Fabricación': lote.fecha_fabricacion,
                'Fecha Caducidad': lote.fecha_caducidad,
                'Días para Caducidad': lote.dias_para_caducidad,
                'Estado': lote.get_estado_display(),
                'Proveedor': lote.orden_suministro.proveedor.razon_social,
                'Fecha Recepción': lote.fecha_recepcion,
            })
        
        # Crear DataFrame
        df = pd.DataFrame(data)
        
        # Crear archivo Excel en memoria
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Inventario', index=False)
            
            # Agregar hoja de resumen
            resumen_data = self._generar_resumen_inventario(lotes)
            resumen_df = pd.DataFrame(resumen_data)
            resumen_df.to_excel(writer, sheet_name='Resumen', index=False)
        
        output.seek(0)
        return output
    
    def _generar_resumen_inventario(self, lotes):
        """Genera datos de resumen para el reporte"""
        hoy = date.today()
        
        # Resumen por institución
        resumen_instituciones = lotes.values(
            'institucion__clue',
            'institucion__denominacion'
        ).annotate(
            total_lotes=Count('id'),
            total_cantidad=Sum('cantidad_disponible'),
            valor_total=Sum('valor_total')
        ).order_by('-valor_total')
        
        # Resumen por categoría
        resumen_categorias = lotes.values(
            'producto__categoria__nombre'
        ).annotate(
            total_lotes=Count('id'),
            total_cantidad=Sum('cantidad_disponible'),
            valor_total=Sum('valor_total')
        ).order_by('-valor_total')
        
        # Alertas de caducidad
        alertas = {
            'Caducados': lotes.filter(fecha_caducidad__lt=hoy).count(),
            'Próximos 30 días': lotes.filter(
                fecha_caducidad__lte=hoy + timedelta(days=30),
                fecha_caducidad__gte=hoy
            ).count(),
            'Próximos 60 días': lotes.filter(
                fecha_caducidad__lte=hoy + timedelta(days=60),
                fecha_caducidad__gt=hoy + timedelta(days=30)
            ).count(),
            'Próximos 90 días': lotes.filter(
                fecha_caducidad__lte=hoy + timedelta(days=90),
                fecha_caducidad__gt=hoy + timedelta(days=60)
            ).count(),
        }
        
        # Combinar todos los datos de resumen
        resumen_data = []
        
        # Agregar resumen general
        resumen_data.append({
            'Tipo': 'RESUMEN GENERAL',
            'Concepto': 'Total de Lotes',
            'Cantidad': lotes.count(),
            'Valor': float(lotes.aggregate(total=Sum('valor_total'))['total'] or 0)
        })
        
        # Agregar alertas
        for alerta, cantidad in alertas.items():
            resumen_data.append({
                'Tipo': 'ALERTAS',
                'Concepto': alerta,
                'Cantidad': cantidad,
                'Valor': 0
            })
        
        # Agregar top instituciones
        for inst in resumen_instituciones[:10]:
            resumen_data.append({
                'Tipo': 'TOP INSTITUCIONES',
                'Concepto': f"{inst['institucion__clue']} - {inst['institucion__denominacion'][:30]}",
                'Cantidad': inst['total_lotes'],
                'Valor': float(inst['valor_total'] or 0)
            })
        
        # Agregar resumen por categorías
        for cat in resumen_categorias:
            resumen_data.append({
                'Tipo': 'POR CATEGORÍA',
                'Concepto': cat['producto__categoria__nombre'],
                'Cantidad': cat['total_lotes'],
                'Valor': float(cat['valor_total'] or 0)
            })
        
        return resumen_data
    
    def generar_reporte_movimientos_excel(self, fecha_desde=None, fecha_hasta=None):
        """Genera reporte de movimientos de inventario"""
        
        movimientos = MovimientoInventario.objects.select_related(
            'lote__producto', 'lote__institucion', 'usuario'
        ).order_by('-fecha_movimiento')
        
        # Aplicar filtros de fecha
        if fecha_desde:
            movimientos = movimientos.filter(fecha_movimiento__gte=fecha_desde)
        if fecha_hasta:
            movimientos = movimientos.filter(fecha_movimiento__lte=fecha_hasta)
        
        # Preparar datos
        data = []
        for mov in movimientos:
            data.append({
                'Fecha': mov.fecha_movimiento,
                'Tipo Movimiento': mov.get_tipo_movimiento_display(),
                'CLUE': mov.lote.institucion.clue,
                'Institución': mov.lote.institucion.denominacion,
                'Clave/CNIS': mov.lote.producto.clave_cnis,
                'Descripción Producto': mov.lote.producto.descripcion,
                'Número Lote': mov.lote.numero_lote,
                'Cantidad': mov.cantidad,
                'Cantidad Anterior': mov.cantidad_anterior,
                'Cantidad Nueva': mov.cantidad_nueva,
                'Motivo': mov.motivo,
                'Documento Referencia': mov.documento_referencia or '',
                'Usuario': mov.usuario.get_full_name() or mov.usuario.username,
            })
        
        # Crear DataFrame y archivo Excel
        df = pd.DataFrame(data)
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Movimientos', index=False)
        
        output.seek(0)
        return output
    
    def generar_reporte_caducidades_excel(self):
        """Genera reporte de productos próximos a caducar"""
        
        hoy = date.today()
        
        # Obtener lotes próximos a caducar
        lotes_caducidad = Lote.objects.select_related(
            'producto', 'institucion'
        ).filter(
            estado=1,
            fecha_caducidad__lte=hoy + timedelta(days=90)
        ).order_by('fecha_caducidad')
        
        data = []
        for lote in lotes_caducidad:
            dias_caducidad = lote.dias_para_caducidad
            
            if dias_caducidad < 0:
                estado_caducidad = 'CADUCADO'
                prioridad = 'CRÍTICA'
            elif dias_caducidad <= 30:
                estado_caducidad = 'PRÓXIMO (30 días)'
                prioridad = 'ALTA'
            elif dias_caducidad <= 60:
                estado_caducidad = 'PRÓXIMO (60 días)'
                prioridad = 'MEDIA'
            else:
                estado_caducidad = 'PRÓXIMO (90 días)'
                prioridad = 'BAJA'
            
            data.append({
                'Prioridad': prioridad,
                'Estado': estado_caducidad,
                'Días para Caducidad': dias_caducidad,
                'CLUE': lote.institucion.clue,
                'Institución': lote.institucion.denominacion,
                'Clave/CNIS': lote.producto.clave_cnis,
                'Descripción': lote.producto.descripcion,
                'Número Lote': lote.numero_lote,
                'Cantidad Disponible': lote.cantidad_disponible,
                'Valor Total': float(lote.valor_total),
                'Fecha Caducidad': lote.fecha_caducidad,
                'Fecha Fabricación': lote.fecha_fabricacion,
            })
        
        # Crear DataFrame y archivo Excel
        df = pd.DataFrame(data)
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Caducidades', index=False)
            
            # Agregar hoja de resumen por prioridad
            resumen_prioridad = df.groupby('Prioridad').agg({
                'Cantidad Disponible': 'sum',
                'Valor Total': 'sum',
                'Número Lote': 'count'
            }).reset_index()
            resumen_prioridad.columns = ['Prioridad', 'Total Cantidad', 'Total Valor', 'Total Lotes']
            resumen_prioridad.to_excel(writer, sheet_name='Resumen Prioridad', index=False)
        
        output.seek(0)
        return output
    
    def generar_estadisticas_dashboard(self):
        """Genera estadísticas para el dashboard"""
        
        hoy = date.today()
        
        # Estadísticas generales
        stats = {
            'total_instituciones': Institucion.objects.filter(activa=True).count(),
            'total_productos': Producto.objects.filter(activo=True).count(),
            'total_lotes': Lote.objects.filter(estado=1).count(),
            'valor_total': Lote.objects.filter(estado=1).aggregate(
                total=Sum('valor_total')
            )['total'] or 0,
        }
        
        # Alertas
        stats['alertas'] = {
            'caducados': Lote.objects.filter(fecha_caducidad__lt=hoy).count(),
            'proximos_30': Lote.objects.filter(
                estado=1,
                fecha_caducidad__lte=hoy + timedelta(days=30),
                fecha_caducidad__gte=hoy
            ).count(),
            'bajo_stock': Lote.objects.filter(
                estado=1,
                cantidad_disponible__lt=10
            ).count(),
        }
        
        # Movimientos recientes
        stats['movimientos_recientes'] = MovimientoInventario.objects.filter(
            fecha_movimiento__gte=hoy - timedelta(days=7)
        ).count()
        
        # Top instituciones por valor
        stats['top_instituciones'] = list(
            Institucion.objects.annotate(
                valor_inventario=Sum('lote__valor_total')
            ).filter(
                activa=True,
                valor_inventario__isnull=False
            ).order_by('-valor_inventario')[:5].values(
                'clue', 'denominacion', 'valor_inventario'
            )
        )
        
        return stats
