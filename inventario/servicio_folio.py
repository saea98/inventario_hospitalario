"""
Servicio para generar folios de citas con formato: IB-YYYY-000001
"""
from datetime import datetime
from .models import CitaProveedor


class ServicioFolio:
    """Servicio para generar folios únicos por año"""
    
    PREFIX = "IB"
    
    @staticmethod
    def generar_folio():
        """
        Genera un folio único con formato: IB-YYYY-000001
        El número se reinicia cada año.
        
        Returns:
            str: Folio generado (ej: IB-2026-000001)
        """
        ahora = datetime.now()
        año = ahora.year
        
        # Buscar el último folio del año actual
        folios_año = CitaProveedor.objects.filter(
            folio__startswith=f"{ServicioFolio.PREFIX}-{año}-"
        ).values_list('folio', flat=True).order_by('-folio')
        
        if folios_año.exists():
            # Extraer el número del último folio
            ultimo_folio = folios_año.first()
            # Formato: IB-2026-000001
            numero = int(ultimo_folio.split('-')[-1])
            siguiente_numero = numero + 1
        else:
            # Es el primer folio del año
            siguiente_numero = 1
        
        # Generar el nuevo folio
        folio = f"{ServicioFolio.PREFIX}-{año}-{siguiente_numero:06d}"
        
        return folio
    
    @staticmethod
    def asignar_folio_a_cita(cita):
        """
        Asigna un folio a una cita si no tiene uno.
        
        Args:
            cita: Instancia de CitaProveedor
            
        Returns:
            str: Folio asignado
        """
        if not cita.folio:
            cita.folio = ServicioFolio.generar_folio()
            cita.save()
        
        return cita.folio
