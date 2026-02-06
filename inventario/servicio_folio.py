"""
Servicio para generar folios de citas con formato: IB-YYYY-000001
"""
from datetime import datetime
from .models import CitaProveedor


class ServicioFolio:
    """Servicio para generar folios únicos por año"""
    
    # Prefijo por defecto (se usa si no se puede determinar por tipo_entrega)
    PREFIX = "IB"
    
    @staticmethod
    def generar_folio(prefix: str = None) -> str:
        """
        Genera un folio único con formato: <PREFIX>-YYYY-000001
        El número se reinicia cada año.
        
        Returns:
            str: Folio generado (ej: IB-2026-000001, T-2026-000001, etc.)
        """
        # Determinar prefijo a usar
        if not prefix:
            prefix = ServicioFolio.PREFIX
        
        ahora = datetime.now()
        año = ahora.year
        
        # Buscar el último folio del año actual
        folios_año = CitaProveedor.objects.filter(
            folio__startswith=f"{prefix}-{año}-"
        ).values_list('folio', flat=True).order_by('-folio')
        
        if folios_año.exists():
            # Extraer el número del último folio
            ultimo_folio = folios_año.first()
            # Formato: PREFIJO-YYYY-000001
            numero = int(ultimo_folio.split('-')[-1])
            siguiente_numero = numero + 1
        else:
            # Es el primer folio del año
            siguiente_numero = 1
        
        # Generar el nuevo folio
        folio = f"{prefix}-{año}-{siguiente_numero:06d}"
        
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
            # Determinar prefijo según el tipo de entrega de la cita
            prefix = ServicioFolio.PREFIX
            try:
                # TIPOS_ENTREGA = [(codigo, descripcion, prefijo), ...]
                mapa_prefijos = {t[0]: t[2] for t in CitaProveedor.TIPOS_ENTREGA}
                if cita.tipo_entrega in mapa_prefijos:
                    prefix = mapa_prefijos[cita.tipo_entrega] or prefix
            except Exception:
                # Si por alguna razón falla el mapeo, se mantiene el prefijo por defecto
                prefix = ServicioFolio.PREFIX

            cita.folio = ServicioFolio.generar_folio(prefix=prefix)
            cita.save()
        
        return cita.folio
