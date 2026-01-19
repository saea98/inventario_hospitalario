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
        from django.db.models import Q
        CitaProveedor = apps.get_model('inventario', 'CitaProveedor')
        
        queryset = CitaProveedor.objects.filter(estado='autorizada').select_related('proveedor')
        
        if self.instance and self.instance.pk:
            queryset = queryset.filter(
                Q(llegada_proveedor__isnull=True) | Q(llegada_proveedor=self.instance)
            )
        else:
            queryset = queryset.exclude(llegada_proveedor__isnull=False)
        
        self.fields['cita'].queryset = queryset.distinct()
    
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
    Formulario para asignar ubicaciones a un item de llegada.
    Permite múltiples ubicaciones con diferentes cantidades (split).
    """
    
    almacen = forms.ModelChoiceField(
        queryset=None,
        label="Almacén",
        required=True,
        empty_label="-- Selecciona un almacén --",
        widget=forms.Select(attrs={
            "class": "form-control select2-single almacen-select",
        })
    )
    
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        from django.apps import apps
        Almacen = apps.get_model('inventario', 'Almacen')

        # Si se pasa un usuario y este tiene un almacén asignado, filtramos
        if user and hasattr(user, 'almacen') and user.almacen:
            self.fields['almacen'].queryset = Almacen.objects.filter(id=user.almacen.id)
            self.fields['almacen'].initial = user.almacen.id
        else:
            # Comportamiento por defecto: mostrar todos los almacenes
            self.fields['almacen'].queryset = Almacen.objects.all().order_by('nombre')


class UbicacionFormSet(BaseFormSet):
    """
    Formset personalizado para manejar ubicaciones de items en llegada.
    Genera dinámicamente un formulario UbicacionItemForm por cada item.
    Permite múltiples ubicaciones por item (split).
    """
    
    def __init__(self, data=None, files=None, llegada=None, user=None, **kwargs):
        self.llegada = llegada
        self.user = user
        self._forms_cache = None
        self._ubicacion_forms_cache = {}
        super().__init__(data=data, files=files, **kwargs)
    
    @property
    def forms(self):
        """Generar formularios dinámicamente basados en los items de la llegada"""
        if self._forms_cache is None:
            self._forms_cache = []
            if self.llegada:
                items = self.llegada.items.all()
                for idx, item in enumerate(items):
                    prefix = f"ubicacion-{idx}"
                    
                    # Preparar datos iniciales si el lote ya existe
                    initial_data = {}
                    if item.lote_creado:
                        initial_data = {
                            'almacen': item.lote_creado.almacen_id,
                        }
                    
                    # Pasar self.data si existe (POST), None si es GET
                    form = UbicacionItemForm(
                        self.data if self.data else None,
                        prefix=prefix,
                        initial=initial_data,
                        user=self.user
                    )
                    self._forms_cache.append(form)
        return self._forms_cache
    
    def get_ubicacion_forms(self, item_index):
        """
        Obtener los formularios de ubicación para un item específico.
        Esto permite múltiples ubicaciones por item.
        """
        if item_index not in self._ubicacion_forms_cache:
            self._ubicacion_forms_cache[item_index] = []
            
            if self.llegada:
                items = self.llegada.items.all()
                if item_index < len(items):
                    item = items[item_index]
                    
                    # Si el lote ya existe, obtener sus ubicaciones
                    if item.lote_creado:
                        ubicaciones_existentes = item.lote_creado.ubicaciones_detalle.all()
                        for idx, ub in enumerate(ubicaciones_existentes):
                            prefix = f"ubicacion-detalle-{item_index}-{idx}"
                            initial_data = {
                                'ubicacion': ub.ubicacion_id,
                                'cantidad': ub.cantidad,
                            }
                            form = UbicacionDetalleForm(
                                self.data if self.data else None,
                                prefix=prefix,
                                initial=initial_data,
                                almacen=item.lote_creado.almacen,
                                cantidad_maxima=item.cantidad_recibida
                            )
                            self._ubicacion_forms_cache[item_index].append(form)
        
        return self._ubicacion_forms_cache[item_index]
    
    def is_valid(self):
        """Validar todos los formularios"""
        if not self.llegada or not self.forms:
            return True
        
        # Validar formularios principales
        main_valid = all(form.is_valid() for form in self.forms)
        
        # Validar formularios de ubicación detalle
        ubicacion_valid = True
        for item_idx in range(len(self.llegada.items.all())):
            ubicacion_forms = self.get_ubicacion_forms(item_idx)
            if not all(form.is_valid() for form in ubicacion_forms):
                ubicacion_valid = False
        
        return main_valid and ubicacion_valid
    
    def get_errors(self):
        """Obtener todos los errores"""
        errors = []
        for form in self.forms:
            if form.errors:
                errors.append(form.errors)
        return errors
