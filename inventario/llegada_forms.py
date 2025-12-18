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
            "tipo_compra": forms.TextInput(attrs={"class": "form-control"}),
        }


class ItemFacturacionForm(forms.ModelForm):
    """
    Formulario para capturar precios de cada item.
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



class UbicacionForm(forms.Form):
    """
    Formulario para asignar ubicación física del lote en almacén.
    Este es un formulario independiente (no ModelForm) porque los campos
    almacen y ubicacion no pertenecen a ItemLlegada, sino a Lote.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from django.apps import apps
        Almacen = apps.get_model('inventario', 'Almacen')
        UbicacionAlmacen = apps.get_model('inventario', 'UbicacionAlmacen')
        
        # Definir los campos en __init__ para asegurar que siempre tengan querysets
        self.fields['almacen'] = forms.ModelChoiceField(
            queryset=Almacen.objects.all().order_by('nombre'),
            label="Almacén",
            required=True,
            widget=forms.Select(attrs={
                "class": "form-control select2-single",
                "data-placeholder": "-- Selecciona un almacén --"
            })
        )
        
        self.fields['ubicacion'] = forms.ModelChoiceField(
            queryset=UbicacionAlmacen.objects.all().order_by('codigo'),
            label="Ubicación",
            required=True,
            widget=forms.Select(attrs={
                "class": "form-control select2-single",
                "data-placeholder": "-- Selecciona una ubicación --"
            })
        )


# Crear un formset personalizado que combine ItemLlegada con UbicacionForm
class UbicacionFormSet(BaseFormSet):
    """Formset personalizado para manejar ubicaciones de items en llegada"""
    
    def __init__(self, data=None, files=None, llegada=None, **kwargs):
        self.llegada = llegada
        self._forms = None
        super().__init__(data=data, files=files, **kwargs)
    
    @property
    def forms(self):
        """Generar formularios dinámicamente basados en los items de la llegada"""
        if self._forms is None:
            self._forms = []
            if self.llegada:
                items = self.llegada.items.all()
                for idx, item in enumerate(items):
                    prefix = f"ubicacion-{idx}"
                    # Pasar self.data si existe (POST), None si es GET
                    form_data = self.data if self.data else None
                    form = UbicacionForm(form_data, prefix=prefix)
                    self._forms.append(form)
        return self._forms
    
    def is_valid(self):
        """Validar todos los formularios"""
        if not self.llegada:
            return True
        # Acceder a forms para asegurar que se generan
        forms = self.forms
        if not forms:
            return True
        return all(form.is_valid() for form in forms)
    
    def save(self):
        """Guardar los datos de ubicación para cada item"""
        if not self.llegada:
            return
        
        items = list(self.llegada.items.all())
        for i, form in enumerate(self.forms):
            if i < len(items) and form.is_valid():
                item = items[i]
                almacen = form.cleaned_data.get('almacen')
                ubicacion = form.cleaned_data.get('ubicacion')
                # Guardar datos temporales en el item para procesarlos en la vista
                item._almacen = almacen
                item._ubicacion = ubicacion
