"""
Servicio para gestionar listas de revisión de citas
"""
from django.utils import timezone
from .models import ListaRevision, ItemRevision


class ServicioListaRevision:
    """Servicio para crear y gestionar listas de revisión"""
    
    # Criterios de revisión por defecto
    CRITERIOS_DEFECTO = [
        ("CLUES correcto", "radio"),
        ("Certificado analítico por lote", "radio"),
        ("Lotes corresponden con certificado analítico", "radio"),
        ("Registro Sanitario vigente o prórroga", "radio"),
        ("Permiso de importación", "radio"),
        ("Registro Sanitario extranjero equivalente", "radio"),
        ("Carta canje con detalle de lotes y piezas", "radio"),
        ("Carta de vicios ocultos con detalle de lotes", "radio"),
    ]
    
    @staticmethod
    def crear_lista_revision(cita, usuario):
        """
        Crear una nueva lista de revisión para una cita.
        
        Args:
            cita: Instancia de CitaProveedor
            usuario: Usuario que crea la lista
            
        Returns:
            Instancia de ListaRevision con items creados
        """
        # Crear lista de revisión
        lista = ListaRevision.objects.create(
            cita=cita,
            folio=cita.folio,  # Usar el mismo folio de la cita
            tipo_documento='factura',
            proveedor=cita.proveedor.razon_social,
            numero_contrato=cita.numero_contrato or '',
            usuario_creacion=usuario,
        )
        
        # Crear items de revisión con criterios por defecto
        items = []
        for orden, (criterio, tipo_control) in enumerate(ServicioListaRevision.CRITERIOS_DEFECTO, 1):
            # Criterios 5 y 6 por defecto en N/A
            resultado = 'na' if orden in [5, 6] else 'si'
            
            item = ItemRevision.objects.create(
                lista_revision=lista,
                descripcion=criterio,
                tipo_control=tipo_control,
                resultado=resultado,
                orden=orden
            )
            items.append(item)
        
        return lista
    
    @staticmethod
    def validar_entrada(lista_revision, usuario, observaciones=''):
        """
        Validar (aprobar) una entrada.
        
        Args:
            lista_revision: Instancia de ListaRevision
            usuario: Usuario que valida
            observaciones: Observaciones finales
        """
        lista_revision.estado = 'aprobada'
        lista_revision.usuario_validacion = usuario
        lista_revision.fecha_validacion = timezone.now()
        lista_revision.observaciones = observaciones
        lista_revision.save()
        
        # Actualizar estado de la cita a autorizada
        cita = lista_revision.cita
        cita.estado = 'autorizada'
        cita.usuario_autorizacion = usuario
        cita.fecha_autorizacion = timezone.now()
        cita.save()
        
        return lista_revision
    
    @staticmethod
    def rechazar_entrada(lista_revision, usuario, justificacion):
        """
        Rechazar una entrada.
        
        Args:
            lista_revision: Instancia de ListaRevision
            usuario: Usuario que rechaza
            justificacion: Justificación del rechazo
        """
        lista_revision.estado = 'rechazada'
        lista_revision.usuario_validacion = usuario
        lista_revision.fecha_validacion = timezone.now()
        lista_revision.justificacion_rechazo = justificacion
        lista_revision.save()
        
        # Actualizar estado de la cita a rechazada (insumo no cumplió criterios; distinto de cancelada)
        cita = lista_revision.cita
        cita.estado = 'rechazada'
        cita.usuario_cancelacion = usuario  # usuario que rechazó
        cita.fecha_cancelacion = timezone.now()
        cita.save()
        
        return lista_revision
