"""
Vistas de prueba para configuración de Telegram
Permite:
- Eliminar webhook
- Obtener Chat ID
- Probar envío de mensajes
"""

import requests
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from .models import ConfiguracionNotificaciones


@login_required
@require_http_methods(["GET", "POST"])
def test_telegram(request):
    """Vista de prueba para Telegram"""
    
    config = ConfiguracionNotificaciones.objects.first()
    
    if not config:
        messages.error(request, "No hay configuración de notificaciones")
        return redirect('admin:inventario_configuracionnotificaciones_change')
    
    resultados = {
        'webhook_eliminado': False,
        'webhook_info': None,
        'updates': None,
        'test_enviado': False,
        'errores': []
    }
    
    if request.method == 'POST':
        accion = request.POST.get('accion')
        
        if accion == 'eliminar_webhook':
            # Eliminar webhook
            url = f"https://api.telegram.org/bot{config.telegram_token}/deleteWebhook"
            try:
                respuesta = requests.post(url, timeout=10)
                resultado = respuesta.json()
                
                if resultado.get('ok'):
                    resultados['webhook_eliminado'] = True
                    messages.success(request, "✓ Webhook eliminado exitosamente")
                else:
                    resultados['errores'].append(f"Error: {resultado.get('description')}")
                    messages.error(request, f"Error: {resultado.get('description')}")
            
            except Exception as e:
                resultados['errores'].append(str(e))
                messages.error(request, f"Error: {str(e)}")
        
        elif accion == 'obtener_updates':
            # Obtener updates para obtener Chat ID
            url = f"https://api.telegram.org/bot{config.telegram_token}/getUpdates"
            try:
                respuesta = requests.get(url, timeout=10)
                resultado = respuesta.json()
                
                if resultado.get('ok'):
                    resultados['updates'] = resultado.get('result', [])
                    
                    if resultados['updates']:
                        messages.success(request, f"✓ Se encontraron {len(resultados['updates'])} actualizaciones")
                    else:
                        messages.warning(request, "No hay actualizaciones. Envía un mensaje al bot en Telegram.")
                else:
                    resultados['errores'].append(f"Error: {resultado.get('description')}")
                    messages.error(request, f"Error: {resultado.get('description')}")
            
            except Exception as e:
                resultados['errores'].append(str(e))
                messages.error(request, f"Error: {str(e)}")
        
        elif accion == 'enviar_test':
            # Enviar mensaje de prueba
            if not config.telegram_chat_id:
                resultados['errores'].append("Chat ID no configurado")
                messages.error(request, "Chat ID no configurado")
            else:
                url = f"https://api.telegram.org/bot{config.telegram_token}/sendMessage"
                datos = {
                    'chat_id': config.telegram_chat_id,
                    'text': '✓ Mensaje de prueba desde Sistema de Inventario Hospitalario',
                    'parse_mode': 'HTML'
                }
                
                try:
                    respuesta = requests.post(url, json=datos, timeout=10)
                    resultado = respuesta.json()
                    
                    if resultado.get('ok'):
                        resultados['test_enviado'] = True
                        messages.success(request, "✓ Mensaje de prueba enviado exitosamente")
                    else:
                        resultados['errores'].append(f"Error: {resultado.get('description')}")
                        messages.error(request, f"Error: {resultado.get('description')}")
                
                except Exception as e:
                    resultados['errores'].append(str(e))
                    messages.error(request, f"Error: {str(e)}")
    
    return render(request, 'inventario/telegram_test.html', {
        'config': config,
        'resultados': resultados
    })


@login_required
def obtener_chat_id_desde_updates(request):
    """API para obtener Chat ID desde updates"""
    
    config = ConfiguracionNotificaciones.objects.first()
    
    if not config:
        return JsonResponse({'error': 'No hay configuración'}, status=400)
    
    url = f"https://api.telegram.org/bot{config.telegram_token}/getUpdates"
    
    try:
        respuesta = requests.get(url, timeout=10)
        resultado = respuesta.json()
        
        if resultado.get('ok'):
            updates = resultado.get('result', [])
            
            if updates:
                # Extraer Chat IDs de los updates
                chat_ids = []
                for update in updates:
                    if 'message' in update:
                        chat_id = update['message'].get('chat', {}).get('id')
                        if chat_id:
                            chat_ids.append({
                                'chat_id': chat_id,
                                'tipo': update['message'].get('chat', {}).get('type'),
                                'titulo': update['message'].get('chat', {}).get('title') or 
                                         update['message'].get('chat', {}).get('first_name'),
                                'mensaje': update['message'].get('text', '')[:50]
                            })
                
                return JsonResponse({
                    'ok': True,
                    'chat_ids': chat_ids,
                    'total': len(chat_ids)
                })
            else:
                return JsonResponse({
                    'ok': False,
                    'error': 'No hay actualizaciones. Envía un mensaje al bot en Telegram.'
                })
        else:
            return JsonResponse({
                'ok': False,
                'error': resultado.get('description')
            })
    
    except Exception as e:
        return JsonResponse({
            'ok': False,
            'error': str(e)
        })
