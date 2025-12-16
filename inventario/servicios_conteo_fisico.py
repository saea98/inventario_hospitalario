"""
Servicios para Conteo Físico

Funciones auxiliares para:
- Validación de conteos
- Cálculo de diferencias
- Generación de reportes
- Auditoría de cambios
"""

from django.db import transaction
from .models import Lote, MovimientoInventario
from datetime import datetime


class ServicioConteoFisico:
    """
    Servicio para gestionar conteos físicos.
    
    Responsabilidades:
    - Validar conteos
    - Calcular diferencias
    - Actualizar existencias
    - Crear auditoría
    """
    
    @staticmethod
    def validar_conteos(primer_conteo, segundo_conteo, tercer_conteo):
        """
        Valida que los conteos sean coherentes.
        
        Args:
            primer_conteo (int): Primer conteo
            segundo_conteo (int): Segundo conteo (opcional)
            tercer_conteo (int): Tercer conteo (definitivo)
        
        Returns:
            dict: {'valido': bool, 'errores': list}
        """
        
        errores = []
        
        if primer_conteo < 0:
            errores.append("El primer conteo no puede ser negativo")
        
        if segundo_conteo and segundo_conteo < 0:
            errores.append("El segundo conteo no puede ser negativo")
        
        if tercer_conteo < 0:
            errores.append("El tercer conteo no puede ser negativo")
        
        # Validar coherencia entre conteos
        if segundo_conteo and abs(primer_conteo - segundo_conteo) > 10:
            # Diferencia mayor a 10 unidades entre primer y segundo conteo
            pass  # Permitir pero registrar en observaciones
        
        return {
            'valido': len(errores) == 0,
            'errores': errores
        }
    
    @staticmethod
    @transaction.atomic
    def registrar_conteo(lote, primer_conteo, segundo_conteo, tercer_conteo, 
                        usuario, observaciones=''):
        """
        Registra un conteo físico y actualiza el inventario.
        
        El TERCER CONTEO es el que se usa como nueva existencia.
        
        Args:
            lote (Lote): Lote a contar
            primer_conteo (int): Primer conteo
            segundo_conteo (int): Segundo conteo (opcional)
            tercer_conteo (int): Tercer conteo (definitivo)
            usuario (User): Usuario que realiza el conteo
            observaciones (str): Observaciones adicionales
        
        Returns:
            MovimientoInventario: Movimiento creado
        
        Raises:
            ValueError: Si hay errores en la validación
        """
        
        # Validar conteos
        validacion = ServicioConteoFisico.validar_conteos(
            primer_conteo, segundo_conteo, tercer_conteo
        )
        
        if not validacion['valido']:
            raise ValueError(f"Errores en validación: {', '.join(validacion['errores'])}")
        
        # Calcular diferencia usando TERCER CONTEO
        cantidad_anterior = lote.cantidad_disponible
        cantidad_nueva = tercer_conteo
        diferencia = cantidad_nueva - cantidad_anterior
        
        # Construir observaciones detalladas
        observaciones_detalladas = f"""Conteo Físico IMSS-Bienestar:
- Primer Conteo: {primer_conteo}
- Segundo Conteo: {segundo_conteo if segundo_conteo else 'No capturado'}
- Tercer Conteo (Definitivo): {tercer_conteo}
- Diferencia: {diferencia:+d} unidades
- Cantidad Anterior: {cantidad_anterior}
- Cantidad Nueva: {cantidad_nueva}"""
        
        if observaciones:
            observaciones_detalladas += f"\n- Observaciones: {observaciones}"
        
        # Crear movimiento
        movimiento = MovimientoInventario.objects.create(
            lote=lote,
            tipo_movimiento='AJUSTE_CONTEO',
            cantidad_anterior=cantidad_anterior,
            cantidad_nueva=cantidad_nueva,
            diferencia=diferencia,
            usuario_creacion=usuario,
            observaciones=observaciones_detalladas
        )
        
        # Actualizar lote
        lote.cantidad_disponible = cantidad_nueva
        lote.valor_total = cantidad_nueva * (lote.precio_unitario or 0)
        lote.save()
        
        return movimiento
    
    @staticmethod
    def calcular_estadisticas_conteos(almacen=None, fecha_desde=None, fecha_hasta=None):
        """
        Calcula estadísticas de conteos realizados.
        
        Args:
            almacen (Almacen): Filtrar por almacén (opcional)
            fecha_desde (date): Fecha inicial (opcional)
            fecha_hasta (date): Fecha final (opcional)
        
        Returns:
            dict: Estadísticas
        """
        
        movimientos = MovimientoInventario.objects.filter(
            tipo_movimiento='AJUSTE_CONTEO'
        )
        
        if almacen:
            movimientos = movimientos.filter(lote__almacen=almacen)
        
        if fecha_desde:
            movimientos = movimientos.filter(fecha_creacion__date__gte=fecha_desde)
        
        if fecha_hasta:
            movimientos = movimientos.filter(fecha_creacion__date__lte=fecha_hasta)
        
        total_conteos = movimientos.count()
        conteos_con_diferencia = movimientos.exclude(diferencia=0).count()
        
        # Diferencias
        diferencias = movimientos.values_list('diferencia', flat=True)
        total_diferencias = sum(abs(d) for d in diferencias if d)
        total_excesos = sum(d for d in diferencias if d and d > 0)
        total_faltantes = sum(abs(d) for d in diferencias if d and d < 0)
        
        # Importes
        total_importe_diferencia = 0
        for mov in movimientos:
            if mov.diferencia:
                importe = mov.diferencia * (mov.lote.precio_unitario or 0)
                total_importe_diferencia += importe
        
        return {
            'total_conteos': total_conteos,
            'conteos_con_diferencia': conteos_con_diferencia,
            'conteos_sin_diferencia': total_conteos - conteos_con_diferencia,
            'total_diferencias': total_diferencias,
            'total_excesos': total_excesos,
            'total_faltantes': total_faltantes,
            'importe_diferencia': total_importe_diferencia,
        }
    
    @staticmethod
    def generar_reporte_conteos(almacen=None, fecha_desde=None, fecha_hasta=None):
        """
        Genera un reporte de conteos en formato de lista.
        
        Args:
            almacen (Almacen): Filtrar por almacén (opcional)
            fecha_desde (date): Fecha inicial (opcional)
            fecha_hasta (date): Fecha final (opcional)
        
        Returns:
            list: Lista de movimientos con información formateada
        """
        
        movimientos = MovimientoInventario.objects.filter(
            tipo_movimiento='AJUSTE_CONTEO'
        ).select_related('lote', 'lote__producto', 'lote__almacen', 'usuario_creacion')
        
        if almacen:
            movimientos = movimientos.filter(lote__almacen=almacen)
        
        if fecha_desde:
            movimientos = movimientos.filter(fecha_creacion__date__gte=fecha_desde)
        
        if fecha_hasta:
            movimientos = movimientos.filter(fecha_creacion__date__lte=fecha_hasta)
        
        reporte = []
        for mov in movimientos.order_by('-fecha_creacion'):
            reporte.append({
                'folio': mov.folio,
                'fecha': mov.fecha_creacion,
                'clave_cnis': mov.lote.producto.clave_cnis,
                'descripcion': mov.lote.producto.nombre,
                'numero_lote': mov.lote.numero_lote,
                'almacen': mov.lote.almacen.nombre,
                'cantidad_anterior': mov.cantidad_anterior,
                'cantidad_nueva': mov.cantidad_nueva,
                'diferencia': mov.diferencia,
                'precio_unitario': mov.lote.precio_unitario or 0,
                'importe_diferencia': (mov.diferencia or 0) * (mov.lote.precio_unitario or 0),
                'usuario': f"{mov.usuario_creacion.first_name} {mov.usuario_creacion.last_name}",
            })
        
        return reporte


# Instancia global del servicio
servicio_conteo = ServicioConteoFisico()
