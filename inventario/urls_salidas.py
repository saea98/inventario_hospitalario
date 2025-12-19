"""
URLs para la Fase 4: Gestión de Salidas y Distribución
"""

from django.urls import path
from . import views_salidas

app_name = 'salidas'

urlpatterns = [
    # Salidas
    path('lista/', views_salidas.lista_salidas, name='lista_salidas'),
    path('crear/', views_salidas.crear_salida, name='crear_salida'),
    path('<uuid:pk>/', views_salidas.detalle_salida, name='detalle_salida'),
    path('<uuid:pk>/autorizar/', views_salidas.autorizar_salida, name='autorizar_salida'),
    path('<uuid:pk>/cancelar/', views_salidas.cancelar_salida, name='cancelar_salida'),
    path('<uuid:pk>/distribuir/', views_salidas.distribuir_salida, name='distribuir_salida'),
    
    # Dashboard
    path('dashboard/', views_salidas.dashboard_salidas, name='dashboard_salidas'),
    
    # APIs para gráficos
    path('api/grafico-estados/', views_salidas.api_grafico_estados, name='api_grafico_estados'),
    path('api/grafico-almacenes/', views_salidas.api_grafico_almacenes, name='api_grafico_almacenes'),
]
