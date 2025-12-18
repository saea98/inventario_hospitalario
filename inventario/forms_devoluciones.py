"""
Formularios para la Fase 2.4: Devoluciones de Proveedores
"""

from django import forms
from django.forms import inlineformset_factory, BaseFormSet
from .models import DevolucionProveedor, ItemDevolucion, Lote, Proveedor


class DevolucionProveedorForm(forms.ModelForm):
    """Formulario para crear/editar devoluciones de proveedor"""
    
    class Meta:
        model = DevolucionProveedor
        fields = [
            'proveedor',
            'motivo_general',
            'descripcion',
            'contacto_proveedor',
            'telefono_proveedor',
            'email_proveedor',
            'fecha_entrega_estimada',
        ]
        widgets = {
            'proveedor': forms.Select(attrs={
                'class': 'form-select select2',
                'required': True,
            }),
            'motivo_general': forms.Select(attrs={
                'class': 'form-select',
                'required': True,
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción detallada de la devolución',
            }),
            'contacto_proveedor': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del contacto en el proveedor',
            }),
            'telefono_proveedor': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Teléfono de contacto',
            }),
            'email_proveedor': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email de contacto',
            }),
            'fecha_entrega_estimada': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
        }
    
    def __init__(self, *args, institucion=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtrar proveedores activos
        self.fields['proveedor'].queryset = Proveedor.objects.filter(activo=True)
        
        # Agregar Select2
        self.fields['proveedor'].widget.attrs['data-placeholder'] = 'Selecciona un proveedor'


class ItemDevolucionForm(forms.ModelForm):
    """Formulario para items de devolución"""
    
    class Meta:
        model = ItemDevolucion
        fields = [
            'lote',
            'cantidad',
            'precio_unitario',
            'motivo_especifico',
        ]
        widgets = {
            'lote': forms.Select(attrs={
                'class': 'form-select select2',
                'required': True,
            }),
            'cantidad': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'required': True,
            }),
            'precio_unitario': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'required': True,
            }),
            'motivo_especifico': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Motivo específico de la devolución de este item',
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtrar lotes disponibles (no caducados, no deteriorados)
        self.fields['lote'].queryset = Lote.objects.filter(
            estado__in=[1]  # Solo disponibles
        ).select_related('producto', 'almacen')
        
        # Agregar Select2
        self.fields['lote'].widget.attrs['data-placeholder'] = 'Selecciona un lote'


class BaseItemDevolucionFormSet(BaseFormSet):
    """FormSet base personalizado para items de devolución"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configurar los formularios
        for form in self.forms:
            form.fields['lote'].queryset = Lote.objects.filter(
                estado__in=[1]  # Solo disponibles
            ).select_related('producto', 'almacen')


# Crear FormSet para items de devolución
ItemDevolucionFormSet = inlineformset_factory(
    DevolucionProveedor,
    ItemDevolucion,
    form=ItemDevolucionForm,
    formset=BaseItemDevolucionFormSet,
    extra=3,
    can_delete=True,
)
