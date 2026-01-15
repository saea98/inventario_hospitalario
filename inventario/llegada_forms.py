"""
Formularios para la Fase 2.2.2: Llegada de Proveedores
"""

from django import forms
from django.forms import inlineformset_factory, BaseFormSet
from .llegada_models import LlegadaProveedor, ItemLlegada, DocumentoLlegada


class LlegadaProveedorForm(forms.ModelForm):
    """
    Formulario para la recepción inicial por parte del Almacenero.
    """
    
    cita = forms.ModelChoiceField(
        queryset=None,  # Se inicializa en __init__
        label="Cita Autorizada",
        widget=forms.Select(attrs={
            "class": "form-control select2-single",
            "data-placeholder": "-- Selecciona una cita --"
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Inicializar queryset dinámicamente
        from django.apps import apps
        CitaProveedor = apps.get_model('inventario', 'CitaProveedor')
        # Filtrar citas autorizadas que no tengan llegada registrada
        self.fields['cita'].queryset = CitaProveedor.objects.filter(
            estado='autorizada'
        ).exclude(
            llegada_proveedor__isnull=False
        ).select_related('proveedor')
    
    class Meta:
        model = LlegadaProveedor
        fields = [
            "cita",
            "remision",
            "numero_piezas_emitidas",
            "numero_piezas_recibidas",
            "observaciones_recepcion",
        ]
        widgets = {
            "remision": forms.TextInput(attrs={"class": "form-control"}),
            "numero_piezas_emitidas": forms.NumberInput(attrs={"class": "form-control"}),
            "numero_piezas_recibidas": forms.NumberInput(attrs={"class": "form-control"}),
            "observaciones_recepcion": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class ItemLlegadaForm(forms.ModelForm):
    """
    Formulario para cada item en la llegada.
    """
    
    producto = forms.ModelChoiceField(
        queryset=None,  # Se inicializa en __init__
        label="Producto",
        widget=forms.Select(attrs={
            "class": "form-control select2-single",
            "data-placeholder": "-- Selecciona un producto --"
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Inicializar queryset dinámicamente
        from django.apps import apps
        Producto = apps.get_model('inventario', 'Producto')
        self.fields['producto'].queryset = Producto.objects.all().order_by('descripcion')
    
    class Meta:
        model = ItemLlegada
        fields = [
            "producto",
            "numero_lote",
            "fecha_caducidad",
            "cantidad_emitida",
            "cantidad_recibida",
            "marca",
            "fabricante",
            "fecha_elaboracion",
        ]
        widgets = {
            "numero_lote": forms.TextInput(attrs={"class": "form-control"}),
            "fecha_caducidad": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "cantidad_emitida": forms.NumberInput(attrs={"class": "form-control"}),
            "cantidad_recibida": forms.NumberInput(attrs={"class": "form-control"}),
            "marca": forms.TextInput(attrs={"class": "form-control"}),
            "fabricante": forms.TextInput(attrs={"class": "form-control"}),
            "fecha_elaboracion": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
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
            "firma_calidad": forms.HiddenInput(),  # Se capturará con JS
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
            "porcentaje_iva": forms.NumberInput(attrs={"class": "form-control"}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Establecer IVA inicial segun la clave del producto
        if self.instance and self.instance.producto:
            clave = self.instance.producto.clave_cnis or ''
            # Claves exentas de IVA
            if any(clave.startswith(prefix) for prefix in ['010', '020', '030', '040']):
                self.fields['porcentaje_iva'].initial = 0.0
            # Todas las demas claves con IVA 0.16
            else:
                self.fields['porcentaje_iva'].initial = 0.16
    
    def clean_porcentaje_iva(self):
        """
        Sobrescribir el valor del IVA con el que corresponde segun la clave CNIS,
        sin importar lo que el usuario haya ingresado.
        """
        if self.instance and self.instance.producto:
            clave = self.instance.producto.clave_cnis or ''
            # Claves exentas de IVA
            if any(clave.startswith(prefix) for prefix in ['010', '020', '030', '040']):
                return 0.0
            # Todas las demas claves con IVA 0.16
            else:
                return 0.16
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
            "descripcion": forms.TextInput(attrs={"class": "form-control"}),
        }


# ============================================================================
# FORMULARIOS PARA ASIGNACIÓN DE UBICACIÓN
# ============================================================================

class UbicacionDetalleForm(forms.Form):
    """
    Formulario para asignar una ubicación y cantidad a un lote.
    Permite múltiples ubicaciones por lote (split).
    """
    
    ubicacion = forms.ModelChoiceField(
        queryset=None,
        label="Ubicación",
        required=True,
        empty_label="-- Selecciona una ubicación --",
        widget=forms.Select(attrs={
            "class": "form-control select2-single ubicacion-select",
        })
    )
    
    cantidad = forms.IntegerField(
        label="Cantidad",
        required=True,
        min_value=1,
        widget=forms.NumberInput(attrs={
            "class": "form-control cantidad-input",
            "placeholder": "Cantidad"
        })
    )
    
    def __init__(self, *args, almacen=None, cantidad_maxima=None, **kwargs):
        super().__init__(*args, **kwargs)
        from django.apps import apps
        UbicacionAlmacen = apps.get_model('inventario', 'UbicacionAlmacen')
        
        # Filtrar ubicaciones por almacén si se proporciona
        if almacen:
            self.fields['ubicacion'].queryset = UbicacionAlmacen.objects.filter(
                almacen=almacen
            ).order_by('codigo')
        else:
            self.fields['ubicacion'].queryset = UbicacionAlmacen.objects.all().order_by('codigo')
        
        # Guardar cantidad máxima para validación
        self.cantidad_maxima = cantidad_maxima
    
    def clean_cantidad(self):
        cantidad = self.cleaned_data.get('cantidad')
        if self.cantidad_maxima and cantidad > self.cantidad_maxima:
            raise forms.ValidationError(
                f"La cantidad no puede exceder {self.cantidad_maxima}"
            )
        return cantidad


class UbicacionItemForm(forms.Form):
    """
    Formulario para asignar ubicación a un item de llegada.
    Este formulario NO es un ModelForm porque los campos almacen y ubicacion
    no pertenecen a ItemLlegada, sino al modelo Lote que se crea después.
    """
    
    almacen = forms.ModelChoiceField(
        queryset=None,
        label="Almacén",
        required=True,
        empty_label="-- Selecciona un almacén --",
        widget=forms.Select(attrs={
            "class": "form-control select2-single",
        })
    )
    
    ubicacion = forms.ModelChoiceField(
        queryset=None,
        label="Ubicación",
        required=True,
        empty_label="-- Selecciona una ubicación --",
        widget=forms.Select(attrs={
            "class": "form-control select2-single ubicacion-select",
        })
    )
    
    cantidad = forms.IntegerField(
        label="Cantidad",
        required=True,
        min_value=1,
        widget=forms.NumberInput(attrs={
            "class": "form-control cantidad-input",
            "placeholder": "Cantidad"
        })
    )
    
    def __init__(self, *args, cantidad_maxima=None, **kwargs):
        super().__init__(*args, **kwargs)
        from django.apps import apps
        Almacen = apps.get_model('inventario', 'Almacen')
        UbicacionAlmacen = apps.get_model('inventario', 'UbicacionAlmacen')
        
        self.fields['almacen'].queryset = Almacen.objects.filter(activo=True).order_by('nombre')
        self.fields['ubicacion'].queryset = UbicacionAlmacen.objects.all().order_by('codigo')
        self.cantidad_maxima = cantidad_maxima
    
    def clean_cantidad(self):
        cantidad = self.cleaned_data.get('cantidad')
        if self.cantidad_maxima and cantidad > self.cantidad_maxima:
            raise forms.ValidationError(
                f"La cantidad no puede exceder {self.cantidad_maxima}"
            )
        return cantidad


class UbicacionFormSet(forms.Form):
    """
    Formulario para múltiples ubicaciones en un item.
    """
    pass
