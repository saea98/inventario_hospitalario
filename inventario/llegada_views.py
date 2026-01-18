

@require_GET
def api_cita_folio(request, cita_id):
    """
    API que devuelve el folio de una cita específica.
    URL: /logistica/llegadas/api/cita/<cita_id>/folio/
    """
    try:
        # Generar folio temporal basado en la cita
        folio = f"TEMP-{cita_id}"
        
        return JsonResponse({
            'folio': folio,
            'cita_id': cita_id
        })
    except Exception as e:
        return JsonResponse({'error': 'Error al obtener folio'}, status=500)
