"""
Formularios para los módulos ENTRADA AL ALMACÉN y PROVEEDURÍA
Versión corregida sin inlineformset_factory
"""

from django import forms
from django.forms import ModelForm
from .models import Lote, MovimientoInventario, Institucion, Almacen, Producto, Proveedor
from datetime import date


class EntradaAlmacenForm(forms.Form):
    """Formulario para la información general de ENTRADA AL ALMACÉN"""
    
    # Información de la Remisión
    numero_remision = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: REM-2024-001',
            'autocomplete': 'off'
        })
    )
    
    fecha_remision = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    numero_pedido = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Opcional'
        })
    )
    
    # Información del Proveedor
    proveedor = forms.ModelChoiceField(
        queryset=Proveedor.objects.filter(activo=True),
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    rfc_proveedor = forms.CharField(
        max_length=13,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Opcional',
            'readonly': True
        })
    )
    
    numero_contrato = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Opcional'
        })
    )
    
    # Destino
    institucion = forms.ModelChoiceField(
        queryset=Institucion.objects.filter(activo=True),
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    almacen = forms.ModelChoiceField(
        queryset=Almacen.objects.filter(activo=True),
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    # Observaciones
    observaciones_generales = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Observaciones adicionales...'
        })
    )


class ProveeduriaForm(forms.Form):
    """Formulario para la información general de PROVEEDURÍA"""
    
    # Información de la Solicitud
    numero_solicitud = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: SOL-2024-001',
            'autocomplete': 'off'
        })
    )
    
    fecha_solicitud = forms.DateField(
        required=True,
        initial=date.today,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    responsable_solicitud = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre del responsable'
        })
    )
    
    # Origen
    institucion_origen = forms.ModelChoiceField(
        queryset=Institucion.objects.filter(activo=True),
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    almacen_origen = forms.ModelChoiceField(
        queryset=Almacen.objects.filter(activo=True),
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    # Destino
    area_destino = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Farmacia, Urgencias, Quirófano'
        })
    )
    
    # Observaciones
    observaciones_generales = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Observaciones adicionales...'
        })
    )


class ItemEntradaForm(forms.Form):
    """Formulario para cada item de ENTRADA AL ALMACÉN"""
    
    producto_id = forms.IntegerField(required=True)
    numero_lote = forms.CharField(max_length=50, required=True)
    cantidad_emitida = forms.IntegerField(required=True, min_value=1)
    cantidad_recibida = forms.IntegerField(required=True, min_value=0)
    fecha_caducidad = forms.DateField(required=False)
    precio_unitario = forms.DecimalField(required=True, min_value=0.01, decimal_places=2)
    subtotal = forms.DecimalField(required=False, decimal_places=2)
    iva = forms.DecimalField(required=False, decimal_places=2)
    importe_total = forms.DecimalField(required=False, decimal_places=2)
    observaciones = forms.CharField(required=False)


class ItemSalidaForm(forms.Form):
    """Formulario para cada item de PROVEEDURÍA"""
    
    lote_id = forms.IntegerField(required=True)
    cantidad_salida = forms.IntegerField(required=True, min_value=1)
    motivo_salida = forms.CharField(max_length=255, required=True)
    observaciones = forms.CharField(required=False)
