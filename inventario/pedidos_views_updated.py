"""
Sección actualizada de la vista crear_solicitud con logging de errores
"""

# Esta es la sección que reemplaza la carga masiva en pedidos_views.py
# Líneas 97-109

def procesar_carga_masiva_csv(request, reader):
    """
    Procesa la carga masiva de CSV con validación y logging de errores.
    """
    from django.db import models
    from .pedidos_utils import registrar_error_pedido
    from .pedidos_models import Producto
    from django.contrib import messages
    
    items_data = []
    
    for row in reader:
        clave = row.get('CLAVE')
        cantidad = row.get('CANTIDAD SOLICITADA')
        
        if clave and cantidad:
            # Validar cantidad
            try:
                cantidad_int = int(cantidad)
            except ValueError:
                registrar_error_pedido(
                    usuario=request.user,
                    tipo_error='CANTIDAD_INVALIDA',
                    clave_solicitada=clave,
                    cantidad_solicitada=None,
                    descripcion_error=f"Cantidad no valida: {cantidad}",
                    enviar_alerta=True
                )
                messages.warning(request, f"La cantidad '{cantidad}' no es valida para la clave '{clave}'.")
                continue
            
            # Buscar producto
            try:
                producto = Producto.objects.get(clave_cnis=clave)
            except Producto.DoesNotExist:
                registrar_error_pedido(
                    usuario=request.user,
                    tipo_error='CLAVE_NO_EXISTE',
                    clave_solicitada=clave,
                    cantidad_solicitada=cantidad_int,
                    descripcion_error=f"La clave '{clave}' no existe en el catalogo de productos.",
                    enviar_alerta=True
                )
                messages.warning(request, f"La clave '{clave}' no existe en el catalogo.")
                continue
            
            # Verificar existencia
            existencia = producto.lotes.filter(estado=1).aggregate(
                total=models.Sum('cantidad_disponible')
            )['total'] or 0
            
            if existencia < cantidad_int:
                registrar_error_pedido(
                    usuario=request.user,
                    tipo_error='SIN_EXISTENCIA',
                    clave_solicitada=clave,
                    cantidad_solicitada=cantidad_int,
                    descripcion_error=f"Existencia insuficiente. Solicitado: {cantidad_int}, Disponible: {existencia}",
                    enviar_alerta=True
                )
                messages.warning(request, f"Existencia insuficiente para '{clave}'. Solicitado: {cantidad_int}, Disponible: {existencia}")
                continue
            
            # Si todo está bien, agregar a items_data
            items_data.append({
                'producto': producto.id,
                'cantidad_solicitada': cantidad_int
            })
    
    return items_data
