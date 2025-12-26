"""
Formularios para Conteo Físico - Validación de Existencias

Basado en el formato IMSS-Bienestar que captura:
- Primer Conteo (validación inicial)
- Segundo Conteo (validación de diferencias)
- Tercer Conteo (valor definitivo que se usa como nueva existencia)
"""

from django import forms
from .models import Lote, Producto, Almacen, UbicacionAlmacen, LoteUbicacion


class BuscarLoteForm(forms.Form):
    """
    Formulario para buscar un lote por CLAVE (CNIS) o NÚMERO DE LOTE.
    
    Si el lote existe, se cargan los datos del sistema.
    Si no existe, se ofrece la opción de crear uno nuevo.
    
    Permite búsqueda por:
    - CLAVE (CNIS) del producto
    - NÚMERO DE LOTE (para personal externo que solo ve el número en las cajas)
    """
    
    TIPO_BUSQUEDA_CHOICES = [
        ('clave', 'Buscar por CLAVE (CNIS)'),
        ('lote', 'Buscar por NÚMERO DE LOTE'),
    ]
    
    tipo_busqueda = forms.ChoiceField(
        label="Tipo de Búsqueda",
        choices=TIPO_BUSQUEDA_CHOICES,
        initial='clave',
        required=True,
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input',
        })
    )
    
    criterio_busqueda = forms.CharField(
        label="Ingrese CLAVE o NÚMERO DE LOTE",
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Ej: 010.000.0104.00 o LT-2025-001',
            'autofocus': True,
            'autocomplete': 'off'
        })
    )
    
    almacen = forms.ModelChoiceField(
        queryset=None,
        required=True,
        label="Almacén",
        widget=forms.Select(attrs={
            'class': 'form-select form-select-lg'
        })
    )
    
    def __init__(self, *args, institucion=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        if institucion:
            self.fields['almacen'].queryset = Almacen.objects.filter(
                institucion=institucion
            ).order_by('nombre')
        else:
            self.fields['almacen'].queryset = Almacen.objects.all().order_by('nombre')


class CapturarConteosForm(forms.Form):
    """
    Formulario para capturar los tres conteos físicos.
    
    Campos:
    - Primer Conteo: Validación inicial
    - Segundo Conteo: Validación de diferencias (opcional)
    - Tercer Conteo: Valor definitivo (obligatorio)
    
    El TERCER CONTEO es el que se usa como nueva existencia.
    """
    
    cifra_primer_conteo = forms.IntegerField(
        label="Primer Conteo",
        min_value=0,
        required=True,
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-lg text-center',
            'placeholder': '0',
            'min': 0,
            'style': 'font-size: 1.2rem; font-weight: bold;'
        })
    )
    
    cifra_segundo_conteo = forms.IntegerField(
        label="Segundo Conteo (Validación)",
        min_value=0,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-lg text-center',
            'placeholder': '0',
            'min': 0,
            'style': 'font-size: 1.2rem;'
        })
    )
    
    tercer_conteo = forms.IntegerField(
        label="Tercer Conteo (DEFINITIVO)",
        min_value=0,
        required=True,
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-lg text-center',
            'placeholder': '0',
            'min': 0,
            'style': 'font-size: 1.5rem; font-weight: bold; border: 3px solid #28a745;'
        })
    )
    
    observaciones = forms.CharField(
        label="Observaciones",
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Notas sobre el conteo (ej: producto dañado, falta de etiqueta, etc.)'
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        primer_conteo = cleaned_data.get('cifra_primer_conteo')
        segundo_conteo = cleaned_data.get('cifra_segundo_conteo')
        tercer_conteo = cleaned_data.get('tercer_conteo')
        
        # Validar que los conteos sean no-negativos
        if primer_conteo is not None and primer_conteo < 0:
            raise forms.ValidationError("El primer conteo no puede ser negativo")
        
        if segundo_conteo is not None and segundo_conteo < 0:
            raise forms.ValidationError("El segundo conteo no puede ser negativo")
        
        if tercer_conteo is not None and tercer_conteo < 0:
            raise forms.ValidationError("El tercer conteo no puede ser negativo")
        
        return cleaned_data


class CrearLoteManualForm(forms.ModelForm):
    """
    Formulario para crear un nuevo lote si no existe en el sistema.
    
    Se utiliza cuando la búsqueda por CLAVE no encuentra resultados.
    """
    
    class Meta:
        model = Lote
        fields = [
            'numero_lote',
            'cantidad_inicial',
            'cantidad_disponible',
            'precio_unitario',
            'valor_total',
            'fecha_fabricacion',
            'fecha_caducidad',
            'fecha_recepcion',
        ]
        widgets = {
            'numero_lote': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número de lote'
            }),
            'cantidad_inicial': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            }),
            'cantidad_disponible': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            }),
            'precio_unitario': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': 0
            }),
            'valor_total': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': 0
            }),
            'fecha_fabricacion': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'fecha_caducidad': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'fecha_recepcion': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }


class FiltroConteosForm(forms.Form):
    """
    Formulario para filtrar conteos realizados.
    """
    
    almacen = forms.ModelChoiceField(
        queryset=None,
        required=False,
        label="Filtrar por Almacén",
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    busqueda = forms.CharField(
        required=False,
        label="Buscar por CLAVE o Lote",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese CLAVE o número de lote'
        })
    )
    
    fecha_desde = forms.DateField(
        required=False,
        label="Desde",
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    fecha_hasta = forms.DateField(
        required=False,
        label="Hasta",
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    def __init__(self, *args, institucion=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        if institucion:
            self.fields['almacen'].queryset = Almacen.objects.filter(
                institucion=institucion
            ).order_by('nombre')
        else:
            self.fields['almacen'].queryset = Almacen.objects.all().order_by('nombre')


class CambiarUbicacionForm(forms.Form):
    nueva_ubicacion = forms.ModelChoiceField(queryset=UbicacionAlmacen.objects.all(), label="Nueva Ubicación")

    def __init__(self, *args, **kwargs):
        almacen = kwargs.pop("almacen", None)
        super().__init__(*args, **kwargs)
        if almacen:
            self.fields["nueva_ubicacion"].queryset = UbicacionAlmacen.objects.filter(almacen=almacen)


class FusionarUbicacionForm(forms.Form):
    lote_destino = forms.ModelChoiceField(queryset=Lote.objects.all(), label="Lote de Destino")

    def __init__(self, *args, **kwargs):
        lote_origen = kwargs.pop("lote_origen", None)
        super().__init__(*args, **kwargs)
        if lote_origen:
            self.fields["lote_destino"].queryset = Lote.objects.filter(
                producto=lote_origen.producto
            ).exclude(id=lote_origen.id)


class AsignarUbicacionForm(forms.Form):
    ubicacion = forms.ModelChoiceField(queryset=UbicacionAlmacen.objects.all(), label="Ubicación")
    cantidad = forms.IntegerField(label="Cantidad", min_value=1)

    def __init__(self, *args, **kwargs):
        almacen = kwargs.pop("almacen", None)
        super().__init__(*args, **kwargs)
        if almacen:
            self.fields["ubicacion"].queryset = UbicacionAlmacen.objects.filter(almacen=almacen)


from django.forms import modelformset_factory

class EditLoteUbicacionForm(forms.ModelForm):
    class Meta:
        model = LoteUbicacion
        fields = ["ubicacion", "cantidad"]
        widgets = {
            "ubicacion": forms.Select(attrs={"class": "form-control"}),
            "cantidad": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
        }

LoteUbicacionFormSet = modelformset_factory(
    LoteUbicacion,
    form=EditLoteUbicacionForm,
    extra=1,
    can_delete=True
)
