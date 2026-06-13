"""Formularios para entradas por transferencia."""

from decimal import Decimal

from django import forms
from django.forms import inlineformset_factory

from .transferencia_models import TransferenciaEntrada, ItemTransferenciaEntrada
from .transferencia_services import resolver_producto_transferencia


def _iva_sugerido_por_clave(clave):
    """Sugerencia de IVA al capturar clave (misma lógica que ItemLlegadaForm)."""
    clave = (clave or '').strip()
    if any(clave.startswith(prefix) for prefix in ('010', '020', '030', '040')):
        return Decimal('0.00')
    if any(clave.startswith(prefix) for prefix in ('060', '080', '130', '379')):
        return Decimal('16.00')
    return Decimal('0.00')


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
            'precio_unitario_sin_iva',
            'porcentaje_iva',
            'precio_unitario_con_iva',
            'subtotal',
            'importe_iva',
            'importe_total',
        ]
        widgets = {
            'numero_lote': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Lote'}),
            'fecha_caducidad': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'cantidad_recibida': forms.NumberInput(
                attrs={'class': 'form-control cantidad-recibida', 'min': '1'}
            ),
            'unidad_medida': forms.TextInput(attrs={'class': 'form-control', 'value': 'Pieza'}),
            'precio_unitario_sin_iva': forms.NumberInput(
                attrs={'class': 'form-control precio-unitario', 'step': '0.01', 'placeholder': '0.00'}
            ),
            'porcentaje_iva': forms.NumberInput(
                attrs={'class': 'form-control porcentaje-iva', 'step': '0.01', 'placeholder': '0.00'}
            ),
            'precio_unitario_con_iva': forms.NumberInput(
                attrs={
                    'class': 'form-control precio-con-iva',
                    'step': '0.01',
                    'placeholder': '0.00',
                    'readonly': 'readonly',
                }
            ),
            'subtotal': forms.NumberInput(
                attrs={
                    'class': 'form-control subtotal',
                    'step': '0.01',
                    'placeholder': '0.00',
                    'readonly': 'readonly',
                }
            ),
            'importe_iva': forms.NumberInput(
                attrs={
                    'class': 'form-control importe-iva',
                    'step': '0.01',
                    'placeholder': '0.00',
                    'readonly': 'readonly',
                }
            ),
            'importe_total': forms.NumberInput(
                attrs={
                    'class': 'form-control importe-total',
                    'step': '0.01',
                    'placeholder': '0.00',
                    'readonly': 'readonly',
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['fecha_caducidad'].required = False
        self.fields['unidad_medida'].required = False
        self.fields['precio_unitario_sin_iva'].required = False
        self.fields['porcentaje_iva'].required = False
        self.fields['precio_unitario_con_iva'].required = False
        self.fields['subtotal'].required = False
        self.fields['importe_iva'].required = False
        self.fields['importe_total'].required = False
        if not self.instance.pk:
            self.fields['unidad_medida'].initial = 'Pieza'
            clave = (self.initial.get('clave') if self.initial else '') or ''
            if clave:
                self.fields['porcentaje_iva'].initial = _iva_sugerido_por_clave(clave)

    def clean_porcentaje_iva(self):
        porcentaje_iva = self.cleaned_data.get('porcentaje_iva')
        if porcentaje_iva is None or porcentaje_iva == '':
            clave = ''
            if self.instance and self.instance.pk and self.instance.clave:
                clave = self.instance.clave
            elif 'clave' in self.cleaned_data:
                clave = self.cleaned_data.get('clave') or ''
            return _iva_sugerido_por_clave(clave)
        return Decimal(str(porcentaje_iva))

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
