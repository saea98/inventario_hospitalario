"""
Formularios para la Fase 4: Gestión de Salidas y Distribución
"""

from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet
from django.core.exceptions import ValidationError
from decimal import Decimal
from .models import (
    SalidaExistencias, ItemSalidaExistencias, DistribucionArea, ItemDistribucion,
    Lote, Almacen, TipoEntrega
)


# ============================================================
# FORMULARIOS PARA SALIDAS
# ============================================================

class FormularioSalida(forms.ModelForm):
    """Formulario para crear/editar salida de existencias"""
    
    class Meta:
        model = SalidaExistencias
        fields = [
            'almacen', 'tipo_entrega', 'fecha_salida_estimada',
            'responsable_salida', 'telefono_responsable', 'email_responsable',
            'observaciones'
        ]
        widgets = {
            'almacen': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'tipo_entrega': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'fecha_salida_estimada': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            'responsable_salida': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del responsable',
                'required': True
            }),
            'telefono_responsable': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Teléfono',
                'type': 'tel'
            }),
            'email_responsable': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'correo@ejemplo.com'
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observaciones adicionales'
            }),
        }
    
    def clean_responsable_salida(self):
        responsable = self.cleaned_data.get('responsable_salida')
        if responsable and len(responsable) < 3:
            raise ValidationError('El nombre del responsable debe tener al menos 3 caracteres.')
        return responsable
    
    def clean_email_responsable(self):
        email = self.cleaned_data.get('email_responsable')
        if email and '@' not in email:
            raise ValidationError('Ingresa un correo electrónico válido.')
        return email


class FormularioItemSalida(forms.ModelForm):
    """Formulario para items de salida"""
    
    lote = forms.ModelChoiceField(
        queryset=Lote.objects.none(),
        widget=forms.Select(attrs={
            'class': 'form-control',
            'required': True
        })
    )
    
    class Meta:
        model = ItemSalidaExistencias
        fields = ['lote', 'cantidad', 'precio_unitario', 'observaciones']
        widgets = {
            'cantidad': forms.NumberInput(attrs={
                'class': 'form-control',
                'type': 'number',
                'min': '1',
                'required': True
            }),
            'precio_unitario': forms.NumberInput(attrs={
                'class': 'form-control',
                'type': 'number',
                'step': '0.01',
                'min': '0',
                'required': True
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Observaciones del item'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        institucion = kwargs.pop('institucion', None)
        super().__init__(*args, **kwargs)
        
        if institucion:
            self.fields['lote'].queryset = Lote.objects.filter(
                almacen__institucion=institucion,
                activo=True,
                cantidad_disponible__gt=0
            ).select_related('producto', 'almacen')
    
    def clean_cantidad(self):
        cantidad = self.cleaned_data.get('cantidad')
        if cantidad and cantidad <= 0:
            raise ValidationError('La cantidad debe ser mayor a 0.')
        return cantidad
    
    def clean_precio_unitario(self):
        precio = self.cleaned_data.get('precio_unitario')
        if precio and precio < 0:
            raise ValidationError('El precio no puede ser negativo.')
        return precio
    
    def clean(self):
        cleaned_data = super().clean()
        lote = cleaned_data.get('lote')
        cantidad = cleaned_data.get('cantidad')
        
        if lote and cantidad:
            if cantidad > lote.cantidad_disponible:
                raise ValidationError(
                    f'La cantidad solicitada ({cantidad}) excede la disponible ({lote.cantidad_disponible}).'
                )
        
        return cleaned_data


class FormularioAutorizarSalida(forms.Form):
    """Formulario para autorizar una salida"""
    
    numero_autorizacion = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Número de autorización',
            'autofocus': True
        })
    )
    
    def clean_numero_autorizacion(self):
        numero = self.cleaned_data.get('numero_autorizacion')
        if numero and len(numero) < 3:
            raise ValidationError('El número de autorización debe tener al menos 3 caracteres.')
        return numero


class FormularioCancelarSalida(forms.Form):
    """Formulario para cancelar una salida"""
    
    motivo_cancelacion = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Motivo de la cancelación',
            'autofocus': True
        })
    )
    
    def clean_motivo_cancelacion(self):
        motivo = self.cleaned_data.get('motivo_cancelacion')
        if motivo and len(motivo) < 10:
            raise ValidationError('El motivo debe tener al menos 10 caracteres.')
        return motivo


# ============================================================
# FORMULARIOS PARA DISTRIBUCIÓN
# ============================================================

class FormularioDistribucion(forms.ModelForm):
    """Formulario para crear distribución a áreas"""
    
    class Meta:
        model = DistribucionArea
        fields = [
            'area_destino', 'responsable_area', 'telefono_responsable',
            'email_responsable', 'fecha_entrega_estimada'
        ]
        widgets = {
            'area_destino': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del área destino',
                'required': True
            }),
            'responsable_area': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del responsable del área',
                'required': True
            }),
            'telefono_responsable': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Teléfono',
                'type': 'tel'
            }),
            'email_responsable': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'correo@ejemplo.com'
            }),
            'fecha_entrega_estimada': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }
    
    def clean_area_destino(self):
        area = self.cleaned_data.get('area_destino')
        if area and len(area) < 3:
            raise ValidationError('El nombre del área debe tener al menos 3 caracteres.')
        return area
    
    def clean_responsable_area(self):
        responsable = self.cleaned_data.get('responsable_area')
        if responsable and len(responsable) < 3:
            raise ValidationError('El nombre del responsable debe tener al menos 3 caracteres.')
        return responsable


class FormularioItemDistribucion(forms.ModelForm):
    """Formulario para items distribuidos"""
    
    class Meta:
        model = ItemDistribucion
        fields = ['cantidad', 'observaciones']
        widgets = {
            'cantidad': forms.NumberInput(attrs={
                'class': 'form-control',
                'type': 'number',
                'min': '1',
                'required': True
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Observaciones'
            }),
        }
    
    def clean_cantidad(self):
        cantidad = self.cleaned_data.get('cantidad')
        if cantidad and cantidad <= 0:
            raise ValidationError('La cantidad debe ser mayor a 0.')
        return cantidad


class FormularioEntregarDistribucion(forms.Form):
    """Formulario para entregar una distribución"""
    
    fecha_entrega = forms.DateTimeField(
        required=True,
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local'
        })
    )
    
    firma_digital = forms.CharField(
        required=False,
        widget=forms.HiddenInput()
    )
    
    observaciones_entrega = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Observaciones de la entrega'
        })
    )


class FormularioRechazarDistribucion(forms.Form):
    """Formulario para rechazar una distribución"""
    
    motivo_rechazo = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Motivo del rechazo',
            'autofocus': True
        })
    )
    
    def clean_motivo_rechazo(self):
        motivo = self.cleaned_data.get('motivo_rechazo')
        if motivo and len(motivo) < 10:
            raise ValidationError('El motivo debe tener al menos 10 caracteres.')
        return motivo


# ============================================================
# FORMSETS
# ============================================================

class FormSetItemsSalida(BaseInlineFormSet):
    """FormSet personalizado para items de salida"""
    
    def clean(self):
        super().clean()
        
        if not self.forms:
            raise ValidationError('Debes agregar al menos un item a la salida.')
        
        # Validar que no haya duplicados
        lotes = []
        for form in self.forms:
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                lote = form.cleaned_data.get('lote')
                if lote and lote in lotes:
                    raise ValidationError('No puedes agregar el mismo lote dos veces.')
                lotes.append(lote)


class FormSetItemsDistribucion(BaseInlineFormSet):
    """FormSet personalizado para items distribuidos"""
    
    def clean(self):
        super().clean()
        
        if not self.forms:
            raise ValidationError('Debes agregar al menos un item a la distribución.')
        
        total_cantidad = 0
        for form in self.forms:
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                cantidad = form.cleaned_data.get('cantidad', 0)
                total_cantidad += cantidad
        
        if total_cantidad == 0:
            raise ValidationError('La cantidad total distribuida debe ser mayor a 0.')


# Crear formsets
ItemSalidaFormSet = inlineformset_factory(
    SalidaExistencias,
    ItemSalidaExistencias,
    form=FormularioItemSalida,
    formset=FormSetItemsSalida,
    extra=1,
    can_delete=True
)

ItemDistribucionFormSet = inlineformset_factory(
    DistribucionArea,
    ItemDistribucion,
    form=FormularioItemDistribucion,
    formset=FormSetItemsDistribucion,
    extra=1,
    can_delete=True
)
