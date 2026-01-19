"""
Formularios para la Fase 2.2.2: Llegada de Proveedores
"""

from django import forms
from django.forms import inlineformset_factory, BaseFormSet
from decimal import Decimal
from .llegada_models import LlegadaProveedor, ItemLlegada, DocumentoLlegada


class LlegadaProveedorForm(forms.ModelForm):
    """
    Formulario para la recepción inicial por parte del Almacenero.
    """
    
    cita = forms.ModelChoiceField(
        queryset=None,
        label="Cita Autorizada",
        widget=forms.Select(attrs={
            "class": "form-control select2-single",
            "data-placeholder": "-- Selecciona una cita --"
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from django.apps import apps
        CitaProveedor = apps.get_model('inventario', 'CitaProveedor')
        self.fields['cita'].queryset = CitaProveedor.objects.filter(
            estado='autorizada'
        ).exclude(
            llegada_proveedor__isnull=False
        ).select_related('proveedor')
    
    class Meta:
        model = LlegadaProveedor
        fields = [
            "cita",
            "proveedor",
            "remision",
            "numero_piezas_emitidas",
            "numero_piezas_recibidas",
            "almacen",
            "tipo_red",
            "numero_orden_suministro",
            "numero_contrato",
            "observaciones_recepcion",
        ]
        widgets = {
            "proveedor": forms.HiddenInput(),
            "remision": forms.TextInput(attrs={"class": "form-control"}),
            "numero_piezas_emitidas": forms.NumberInput(attrs={"class": "form-control"}),
            "numero_piezas_recibidas": forms.NumberInput(attrs={"class": "form-control"}),
            "almacen": forms.Select(attrs={"class": "form-control select2-single"}),
            "tipo_red": forms.Select(attrs={"class": "form-control"}),
            "numero_orden_suministro": forms.TextInput(attrs={"class": "form-control"}),
            "numero_contrato": forms.TextInput(attrs={"class": "form-control"}),
            "observaciones_recepcion": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class ItemLlegadaForm(forms.ModelForm):
    """
    Formulario para cada item en la llegada.
    Incluye campos para cálculos de IVA y precios.
    """
    
    producto = forms.ModelChoiceField(
        queryset=None,
        label="Producto",
        widget=forms.Select(attrs={
            "class": "form-control select2-single",
            "data-placeholder": "-- Selecciona un producto --"
        })
    )
    
    clave = forms.CharField(
        label="Clave CNIS",
        required=True,
        widget=forms.TextInput(attrs={
            "class": "form-control clave-cnis",
            "placeholder": "Heredada de la cita"
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from django.apps import apps
        Producto = apps.get_model('inventario', 'Producto')
        self.fields['producto'].queryset = Producto.objects.all().order_by('descripcion')
    
    class Meta:
        model = ItemLlegada
        fields = [
            "producto",
            "clave",
            "numero_lote",
            "marca",
            "fabricante",
            "fecha_elaboracion",
            "fecha_caducidad",
            "cantidad_emitida",
            "cantidad_recibida",
            "piezas_por_lote",
            "precio_unitario_sin_iva",
            "porcentaje_iva",
            "precio_unitario_con_iva",
            "subtotal",
            "importe_iva",
            "importe_total",
        ]
        widgets = {
            "numero_lote": forms.TextInput(attrs={"class": "form-control numero-lote"}),
            "marca": forms.TextInput(attrs={"class": "form-control"}),
            "fabricante": forms.TextInput(attrs={"class": "form-control"}),
            "fecha_elaboracion": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "fecha_caducidad": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "cantidad_emitida": forms.NumberInput(attrs={"class": "form-control cantidad-emitida"}),
            "cantidad_recibida": forms.NumberInput(attrs={"class": "form-control cantidad-recibida"}),
            "piezas_por_lote": forms.NumberInput(attrs={"class": "form-control piezas-por-lote", "min": "1"}),
            "precio_unitario_sin_iva": forms.NumberInput(attrs={
                "class": "form-control precio-unitario",
                "step": "0.01",
                "placeholder": "0.00"
            }),
            "porcentaje_iva": forms.NumberInput(attrs={
                "class": "form-control porcentaje-iva",
                "step": "0.01",
                "placeholder": "0.00",
                "readonly": "readonly"
            }),
            "precio_unitario_con_iva": forms.NumberInput(attrs={
                "class": "form-control precio-con-iva",
                "step": "0.01",
                "placeholder": "0.00",
                "readonly": "readonly"
            }),
            "subtotal": forms.NumberInput(attrs={
                "class": "form-control subtotal",
                "step": "0.01",
                "placeholder": "0.00",
                "readonly": "readonly"
            }),
            "importe_iva": forms.NumberInput(attrs={
                "class": "form-control importe-iva",
                "step": "0.01",
                "placeholder": "0.00",
                "readonly": "readonly"
            }),
            "importe_total": forms.NumberInput(attrs={
                "class": "form-control importe-total",
                "step": "0.01",
                "placeholder": "0.00",
                "readonly": "readonly"
            }),
        }


ItemLlegadaFormSet = inlineformset_factory(
    LlegadaProveedor,
    ItemLlegada,
    form=ItemLlegadaForm,
    extra=1,
    can_delete=True,
    can_delete_extra=True,
    fk_name="llegada",
    min_num=1,
    validate_min=True,
)


class ControlCalidadForm(forms.ModelForm):
    """
    Formulario para la validación de Control de Calidad.
    """
    
    class Meta:
        model = LlegadaProveedor
        fields = [
            "estado_calidad",
            "observaciones_calidad",
            "firma_calidad",
        ]
        widgets = {
            "estado_calidad": forms.Select(attrs={"class": "form-control"}),
            "observaciones_calidad": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "firma_calidad": forms.HiddenInput(),
        }


TIPO_ENTRADA_CHOICES = [
    ('', '-- Selecciona tipo de entrada --'),
    ('Entrega directa', 'Entrega directa'),
    ('Operador Logístico', 'Operador Logístico'),
    ('Sedesa', 'Sedesa'),
    ('Transferencia', 'Transferencia'),
    ('Canje', 'Canje'),
    ('Donación', 'Donación'),
]


class FacturacionForm(forms.ModelForm):
    """
    Formulario para la captura de datos de Facturación.
    """
    
    class Meta:
        model = LlegadaProveedor
        fields = [
            "numero_factura",
            "numero_orden_suministro",
            "numero_contrato",
            "numero_procedimiento",
            "programa_presupuestario",
            "tipo_compra",
        ]
        widgets = {
            "numero_factura": forms.TextInput(attrs={"class": "form-control"}),
            "numero_orden_suministro": forms.TextInput(attrs={"class": "form-control"}),
            "numero_contrato": forms.TextInput(attrs={"class": "form-control"}),
            "numero_procedimiento": forms.TextInput(attrs={"class": "form-control"}),
            "programa_presupuestario": forms.TextInput(attrs={"class": "form-control"}),
            "tipo_compra": forms.Select(choices=TIPO_ENTRADA_CHOICES, attrs={"class": "form-control"}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tipo_compra'].label = 'Tipo de Entrada'
        self.fields['tipo_compra'].choices = TIPO_ENTRADA_CHOICES


class ItemFacturacionForm(forms.ModelForm):
    """
    Formulario para capturar precios de cada item.
    El IVA se asigna automaticamente segun la clave CNIS del producto.
    """
    
    class Meta:
        model = ItemLlegada
        fields = [
            "precio_unitario_sin_iva",
            "porcentaje_iva",
        ]
        widgets = {
            "precio_unitario_sin_iva": forms.NumberInput(attrs={"class": "form-control"}),
            "porcentaje_iva": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.producto:
            clave = self.instance.producto.clave_cnis or ''
            if any(clave.startswith(prefix) for prefix in ['010', '020', '030', '040']):
                self.fields['porcentaje_iva'].initial = Decimal('0.00')
            else:
                self.fields['porcentaje_iva'].initial = Decimal('0.16')
    
    def clean_porcentaje_iva(self):
        """
        Sobrescribir el valor del IVA con el que corresponde segun la clave CNIS.
        """
        if self.instance and self.instance.producto:
            clave = self.instance.producto.clave_cnis or ''
            if any(clave.startswith(prefix) for prefix in ['010', '020', '030', '040']):
                return Decimal('0.00')
            else:
                return Decimal('0.16')
        return self.cleaned_data.get('porcentaje_iva')


ItemFacturacionFormSet = inlineformset_factory(
    LlegadaProveedor,
    ItemLlegada,
    form=ItemFacturacionForm,
    extra=0,
    can_delete=False,
    fk_name="llegada",
)


class SupervisionForm(forms.ModelForm):
    """
    Formulario para la validación de Supervisión.
    """
    
    class Meta:
        model = LlegadaProveedor
        fields = [
            "estado_supervision",
            "observaciones_supervision",
            "firma_supervision",
        ]
        widgets = {
            "estado_supervision": forms.Select(attrs={"class": "form-control"}),
            "observaciones_supervision": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "firma_supervision": forms.HiddenInput(),
        }


class DocumentoLlegadaForm(forms.ModelForm):
    """
    Formulario para subir documentos adjuntos.
    """
    
    class Meta:
        model = DocumentoLlegada
        fields = ["tipo_documento", "archivo", "descripcion"]
        widgets = {
            "tipo_documento": forms.Select(attrs={"class": "form-control"}),
            "archivo": forms.FileInput(attrs={"class": "form-control-file"}),
            "descripcion": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }
