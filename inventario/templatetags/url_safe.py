"""
Template tags seguros para URLs que pueden no existir
"""

from django import template
from django.urls import reverse, NoReverseMatch

register = template.Library()


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
