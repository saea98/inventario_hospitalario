"""Formularios para entradas por transferencia."""

from django import forms
from django.forms import inlineformset_factory

from .transferencia_models import TransferenciaEntrada, ItemTransferenciaEntrada
from .transferencia_services import resolver_producto_transferencia


class TransferenciaEntradaForm(forms.ModelForm):
    class Meta:
        model = TransferenciaEntrada
        fields = [
            'remision',
            'almacen_destino',
            'entidad_origen',
            'estado_origen',
            'fecha_recepcion',
            'numero_piezas_recibidas',
            'observaciones',
        ]
        widgets = {
            'remision': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número de remisión'}),
            'almacen_destino': forms.Select(attrs={'class': 'form-control select2-single'}),
            'entidad_origen': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Ej. Almacén Vallejo, IMSS Jalisco'}
            ),
            'estado_origen': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Opcional'}),
            'fecha_recepcion': forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M',
            ),
            'numero_piezas_recibidas': forms.NumberInput(
                attrs={'class': 'form-control', 'min': '0', 'placeholder': 'Opcional'}
            ),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import Almacen

        self.fields['almacen_destino'].queryset = Almacen.objects.filter(activo=True).order_by('nombre')
        self.fields['numero_piezas_recibidas'].required = False
        self.fields['estado_origen'].required = False
        self.fields['observaciones'].required = False


class ItemTransferenciaEntradaForm(forms.ModelForm):
    clave = forms.CharField(
        label='Clave CNIS',
        widget=forms.TextInput(attrs={'class': 'form-control clave-cnis', 'placeholder': 'Clave'}),
    )
    descripcion = forms.CharField(
        label='Descripción',
        required=False,
        widget=forms.TextInput(
            attrs={'class': 'form-control descripcion-item', 'placeholder': 'Opcional si está en catálogo'}
        ),
    )

    class Meta:
        model = ItemTransferenciaEntrada
        fields = [
            'clave',
            'descripcion',
            'numero_lote',
            'fecha_caducidad',
            'cantidad_recibida',
            'unidad_medida',
        ]
        widgets = {
            'numero_lote': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Lote'}),
            'fecha_caducidad': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'cantidad_recibida': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'unidad_medida': forms.TextInput(attrs={'class': 'form-control', 'value': 'Pieza'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['fecha_caducidad'].required = False
        self.fields['unidad_medida'].required = False
        if not self.instance.pk:
            self.fields['unidad_medida'].initial = 'Pieza'

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('DELETE'):
            return cleaned

        clave = (cleaned.get('clave') or '').strip()
        cantidad = cleaned.get('cantidad_recibida')
        numero_lote = (cleaned.get('numero_lote') or '').strip()

        if not clave and not cantidad and not numero_lote:
            return cleaned

        if not clave:
            self.add_error('clave', 'Indique la clave CNIS.')
            return cleaned
        if not numero_lote:
            self.add_error('numero_lote', 'Indique el número de lote.')
            return cleaned
        if not cantidad or cantidad < 1:
            self.add_error('cantidad_recibida', 'La cantidad debe ser al menos 1.')
            return cleaned

        descripcion = (cleaned.get('descripcion') or '').strip()
        cleaned['producto'] = resolver_producto_transferencia(clave, descripcion)
        cleaned['clave'] = clave
        if not descripcion:
            cleaned['descripcion'] = cleaned['producto'].descripcion
        if not cleaned.get('unidad_medida'):
            cleaned['unidad_medida'] = 'Pieza'
        return cleaned

    def save(self, commit=True):
        self.instance.producto = self.cleaned_data['producto']
        self.instance.clave = self.cleaned_data['clave']
        if self.cleaned_data.get('descripcion'):
            self.instance.descripcion = self.cleaned_data['descripcion']
        return super().save(commit=commit)


ItemTransferenciaEntradaFormSet = inlineformset_factory(
    TransferenciaEntrada,
    ItemTransferenciaEntrada,
    form=ItemTransferenciaEntradaForm,
    extra=1,
    can_delete=True,
    can_delete_extra=True,
    fk_name='transferencia',
    min_num=1,
    validate_min=True,
)
