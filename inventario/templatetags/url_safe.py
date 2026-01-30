"""
Template tags seguros para URLs que pueden no existir
"""

from django import template
from django.urls import reverse, NoReverseMatch
from urllib.parse import urlencode

register = template.Library()


@register.simple_tag
def url_sort_citas(request, columna, ordenar_actual, dir_actual):
    """
    Construye la URL para ordenar por columna. Si ya se ordena por esa columna, alterna asc/desc.
    Uso: {% url_sort_citas request 'proveedor' ordenar_actual dir_actual %}
    """
    params = request.GET.copy()
    params['ordenar'] = columna
    if ordenar_actual == columna:
        params['dir'] = 'asc' if dir_actual == 'desc' else 'desc'
    else:
        params['dir'] = 'asc'
    return '?' + params.urlencode()


@register.filter
def url_segura(url_name):
    """
    Intenta obtener la URL, si no existe retorna #
    
    Uso en template:
    <a href="{{ item.url_name|url_segura }}">{{ item.nombre_mostrado }}</a>
    """
    try:
        return reverse(url_name)
    except NoReverseMatch:
        return '#'


@register.simple_tag
def obtener_url_segura(url_name):
    """
    Obtiene la URL de forma segura, retorna # si no existe
    
    Uso en template:
    {% obtener_url_segura item.url_name as url %}
    <a href="{{ url }}">{{ item.nombre_mostrado }}</a>
    """
    try:
        return reverse(url_name)
    except NoReverseMatch:
        return '#'
