from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Div, HTML
from crispy_forms.bootstrap import Field
#from django_select2.forms import ModelSelect2Widget, Select2MultipleWidget
from django_select2.forms import Select2Widget, ModelSelect2Widget

from .models import (
    Institucion, Producto, Proveedor, Lote, OrdenSuministro,
    CategoriaProducto, Alcaldia, TipoInstitucion, FuenteFinanciamiento,
    MovimientoInventario, CargaInventario, TipoInstitucion, UbicacionAlmacen,
    CitaProveedor, OrdenTraslado, ConteoFisico, ItemConteoFisico, TipoRed, TipoEntrega
)
#from .models import Institucion, Alcaldia, TipoInstitucion


class InstitucionForm(forms.ModelForm):
    class Meta:
        model = Institucion
        fields = ['clue', 'ib_clue', 'denominacion', 'alcaldia', 'tipo_institucion', 
                 'direccion', 'telefono', 'email', 'activo']
        widgets = {
            'direccion': forms.Textarea(attrs={'rows': 3}),
            'clue': forms.TextInput(attrs={'placeholder': 'Ej: DFIMB002324'}),
            'ib_clue': forms.TextInput(attrs={'placeholder': 'Ej: DFIMB002324'}),
            'denominacion': forms.TextInput(attrs={'placeholder': 'Nombre completo de la institución'}),
            'telefono': forms.TextInput(attrs={'placeholder': '55-1234-5678'}),
            'email': forms.EmailInput(attrs={'placeholder': 'contacto@institucion.gob.mx'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('clue', css_class='form-group col-md-6 mb-0'),
                Column('ib_clue', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            'denominacion',
            Row(
                Column('alcaldia', css_class='form-group col-md-6 mb-0'),
                Column('tipo_institucion', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            'direccion',
            Row(
                Column('telefono', css_class='form-group col-md-6 mb-0'),
                Column('email', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            'activo',
            Submit('submit', 'Guardar Institución', css_class='btn btn-primary')
        )


# forms.py
class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = [
            'clave_cnis',
            'descripcion',
            'categoria',
            'unidad_medida',
            'es_insumo_cpm',
            'precio_unitario_referencia',
            'clave_saica',
            'descripcion_saica',
            'unidad_medida_saica',
            'proveedor',
            'rfc_proveedor',
            'partida_presupuestal',
            'marca',
            'fabricante',
            'cantidad_disponible',
            'activo'
        ]
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
            'descripcion_saica': forms.Textarea(attrs={'rows': 2}),
            'clave_cnis': forms.TextInput(attrs={'placeholder': 'Ej: 010.000.0022.00'}),
            'clave_saica': forms.TextInput(attrs={'placeholder': 'Ej: 1234-SAICA'}),
            'precio_unitario_referencia': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'cantidad_disponible': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'unidad_medida': forms.TextInput(attrs={'placeholder': 'Ej: PIEZA'}),
            'unidad_medida_saica': forms.TextInput(attrs={'placeholder': 'Ej: CAJA, LITRO, etc.'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Row(
                Column('clave_cnis', css_class='form-group col-md-6 mb-0'),
                Column('categoria', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            'descripcion',
            Row(
                Column('unidad_medida', css_class='form-group col-md-4 mb-0'),
                Column('precio_unitario_referencia', css_class='form-group col-md-4 mb-0'),
                Column(
                    Div(
                        'es_insumo_cpm',
                        'activo',
                        css_class='mt-3'
                    ),
                    css_class='form-group col-md-4 mb-0'
                ),
                css_class='form-row'
            ),
            HTML("<hr><h5>Datos complementarios</h5>"),
            Row(
                Column('clave_saica', css_class='form-group col-md-6 mb-0'),
                Column('descripcion_saica', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('unidad_medida_saica', css_class='form-group col-md-4 mb-0'),
                Column('proveedor', css_class='form-group col-md-4 mb-0'),
                Column('rfc_proveedor', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('partida_presupuestal', css_class='form-group col-md-4 mb-0'),
                Column('marca', css_class='form-group col-md-4 mb-0'),
                Column('fabricante', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('cantidad_disponible', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Submit('submit', 'Guardar Producto', css_class='btn btn-primary')
        )




class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = ['rfc', 'razon_social', 'direccion', 'telefono', 'email', 
                 'contacto_principal', 'activo']
        widgets = {
            'direccion': forms.Textarea(attrs={'rows': 3}),
            'rfc': forms.TextInput(attrs={'placeholder': 'Ej: ABC123456789'}),
            'razon_social': forms.TextInput(attrs={'placeholder': 'Nombre de la empresa'}),
            'telefono': forms.TextInput(attrs={'placeholder': '55-1234-5678'}),
            'email': forms.EmailInput(attrs={'placeholder': 'contacto@proveedor.com'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('rfc', css_class='form-group col-md-6 mb-0'),
                Column('razon_social', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            'direccion',
            Row(
                Column('telefono', css_class='form-group col-md-4 mb-0'),
                Column('email', css_class='form-group col-md-4 mb-0'),
                Column('contacto_principal', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            'activo',
            Submit('submit', 'Guardar Proveedor', css_class='btn btn-primary')
        )


class LoteForm(forms.ModelForm):
    class Meta:
        model = Lote
        exclude = ['uuid', 'fecha_creacion', 'fecha_actualizacion', 'creado_por',
                   'fecha_cambio_estado', 'usuario_cambio_estado', 'valor_total']
        widgets = {
            'fecha_fabricacion': forms.DateInput(
                attrs={'type': 'date'},
                format='%Y-%m-%d'
            ),
            'fecha_caducidad': forms.DateInput(
                attrs={'type': 'date'}, 
                format='%Y-%m-%d'
            ),
            'fecha_recepcion': forms.DateInput(
                attrs={'type': 'date'},
                format='%Y-%m-%d'
            ),
            'fecha_fabricacion_csv': forms.DateInput(
                attrs={'type': 'date'},
                format='%Y-%m-%d'
            ),
            'precio_unitario': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'cantidad_inicial': forms.NumberInput(attrs={'min': '1'}),
            'cantidad_disponible': forms.NumberInput(attrs={'min': '0'}),
            'observaciones': forms.Textarea(attrs={'rows': 3}),
            'motivo_cambio_estado': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Establecer formatos de entrada para campos de fecha
        date_fields = ['fecha_fabricacion', 'fecha_caducidad', 'fecha_recepcion', 'fecha_fabricacion_csv']
        for field_name in date_fields:
            self.fields[field_name].input_formats = ['%Y-%m-%d']  # Formato YYYY-MM-DD
            
            # Si hay una instancia con fechas, formatearlas correctamente para el widget
            if self.instance and getattr(self.instance, field_name):
                try:
                    self.initial[field_name] = getattr(self.instance, field_name).strftime('%Y-%m-%d')
                except (AttributeError, ValueError):
                    # Si hay algún error, mantener el valor actual
                    pass

        # Filtrado dinámico de ubicaciones según el almacén
        if 'almacen' in self.data:
            try:
                almacen_id = int(self.data.get('almacen'))
                self.fields['ubicacion'].queryset = UbicacionAlmacen.objects.filter(
                    almacen_id=almacen_id,
                    activo=True
                ).order_by('codigo')
            except (ValueError, TypeError):
                self.fields['ubicacion'].queryset = UbicacionAlmacen.objects.none()
        elif self.instance.pk and self.instance.almacen:
            self.fields['ubicacion'].queryset = UbicacionAlmacen.objects.filter(
                almacen=self.instance.almacen,
                activo=True
            ).order_by('codigo')
        else:
            self.fields['ubicacion'].queryset = UbicacionAlmacen.objects.none()

        self.helper = FormHelper()
        self.helper.layout = Layout(
            HTML("<h5 class='mt-3 text-primary'>Información General</h5>"),
            Row(
                Column('numero_lote', css_class='col-md-3'),
                Column('producto', css_class='col-md-3'),
                Column('institucion', css_class='col-md-3'),
                Column('almacen', css_class='col-md-3')
            ),
            Row(
                Column('ubicacion', css_class='col-md-4'),
                Column('orden_suministro', css_class='col-md-4'),
                Column('estado', css_class='col-md-4')
            ),
            'motivo_cambio_estado',
            'observaciones',

            HTML("<h5 class='mt-4 text-primary'>Cantidades y Fechas</h5>"),
            Row(
                Column('cantidad_inicial', css_class='col-md-3'),
                Column('cantidad_disponible', css_class='col-md-3'),
                Column('precio_unitario', css_class='col-md-3'),
                Column('fecha_recepcion', css_class='col-md-3')
            ),
            Row(
                Column('fecha_fabricacion', css_class='col-md-4'),
                Column('fecha_caducidad', css_class='col-md-4'),
                Column('fecha_fabricacion_csv', css_class='col-md-4')
            ),

            HTML("<h5 class='mt-4 text-primary'>Datos SAICA</h5>"),
            Row(
                Column('cns', css_class='col-md-4'),
                Column('proveedor', css_class='col-md-4'),
                Column('rfc_proveedor', css_class='col-md-4')
            ),
            Row(
                Column('partida', css_class='col-md-4'),
                Column('clave_saica', css_class='col-md-4'),
                Column('descripcion_saica', css_class='col-md-4')
            ),
            Row(
                Column('unidad_saica', css_class='col-md-4'),
                Column('fuente_datos', css_class='col-md-4')
            ),

            HTML("<h5 class='mt-4 text-primary'>Información del Pedido</h5>"),
            Row(
                Column('contrato', css_class='col-md-3'),
                Column('folio', css_class='col-md-3'),
                Column('pedido', css_class='col-md-3'),
                Column('remision', css_class='col-md-3')
            ),
            Row(
                Column('licitacion', css_class='col-md-4'),
                Column('responsable', css_class='col-md-4'),
                Column('reviso', css_class='col-md-4')
            ),
            Row(
                Column('tipo_entrega', css_class='col-md-4'),
                Column('tipo_red', css_class='col-md-4'),
                Column('epa', css_class='col-md-4')
            ),
            Row(
                Column('subtotal', css_class='col-md-4'),
                Column('iva', css_class='col-md-4'),
                Column('importe_total', css_class='col-md-4')
            ),

            Submit('submit', 'Guardar cambios', css_class='btn btn-primary mt-3')
        )

    def clean(self):
        cleaned_data = super().clean()
        cantidad_inicial = cleaned_data.get('cantidad_inicial')
        cantidad_disponible = cleaned_data.get('cantidad_disponible')
        fecha_fabricacion = cleaned_data.get('fecha_fabricacion')
        fecha_caducidad = cleaned_data.get('fecha_caducidad')

        if cantidad_inicial and cantidad_disponible and cantidad_disponible > cantidad_inicial:
            raise forms.ValidationError("La cantidad disponible no puede ser mayor que la cantidad inicial.")

        if fecha_fabricacion and fecha_caducidad and fecha_fabricacion >= fecha_caducidad:
            raise forms.ValidationError("La fecha de fabricación debe ser anterior a la de caducidad.")

        return cleaned_data

class LoteChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        desc = obj.descripcion_saica or obj.producto.descripcion
        return f"{obj.numero_lote} — {desc}"



class LoteSelectWidget(ModelSelect2Widget):
    model = Lote
    search_fields = [
        "numero_lote__icontains",
        "descripcion_saica__icontains",
        "producto__descripcion__icontains",
        "institucion__denominacion__icontains",
    ]

    def label_from_instance(self, obj):
        desc = obj.descripcion_saica or obj.producto.descripcion
        return f"{obj.numero_lote} — {desc}"


class InstitucionDestinoWidget(ModelSelect2Widget):
    model = Institucion
    search_fields = [
        'clue__icontains',
        'denominacion__icontains',
        'municipio__icontains',
    ]

    def label_from_instance(self, obj):
        return f"{obj.clue} — {obj.denominacion}"


class MovimientoInventarioForm(forms.ModelForm):
    class Meta:
        model = MovimientoInventario
        fields = [
            'lote', 'tipo_movimiento', 'cantidad', 'motivo',
            'documento_referencia', 'institucion_destino'
        ]

        widgets = {
            'lote': LoteSelectWidget(),  # 👈 INSTANCIA

            'tipo_movimiento': Select2Widget(),

            'cantidad': forms.NumberInput(attrs={'min': '1'}),

            'motivo': forms.Textarea(attrs={'rows': 3}),

            'institucion_destino': InstitucionDestinoWidget(),  # 👈 INSTANCIA
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Queryset base (aunque AJAX lo sobreescribe)
        self.fields['lote'].queryset = Lote.objects.select_related("producto")

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('lote', css_class='form-group col-md-6 mb-0'),
                Column('tipo_movimiento', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('cantidad', css_class='form-group col-md-6 mb-0'),
                Column('documento_referencia', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            'institucion_destino',
            'motivo',
            Submit('submit', 'Registrar Movimiento', css_class='btn btn-primary')
        )




class CargaInventarioForm(forms.ModelForm):
    class Meta:
        model = CargaInventario
        fields = ['archivo']
        widgets = {
            'archivo': forms.FileInput(attrs={'accept': '.xlsx,.xls'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            HTML('<div class="alert alert-info">'),
            HTML('<strong>Instrucciones:</strong> Seleccione un archivo Excel (.xlsx o .xls) con el formato de inventario hospitalario.'),
            HTML('</div>'),
            'archivo',
            Submit('submit', 'Cargar Archivo', css_class='btn btn-success')
        )


class FiltroInventarioForm(forms.Form):
    institucion = forms.ModelChoiceField(
        queryset=Institucion.objects.filter(activo=True),
        required=False,
        empty_label="Todas las instituciones"
    )
    producto = forms.ModelChoiceField(
        queryset=Producto.objects.filter(activo=True),
        required=False,
        empty_label="Todos los productos"
    )
    categoria = forms.ModelChoiceField(
        queryset=CategoriaProducto.objects.all(),
        required=False,
        empty_label="Todas las categorías"
    )
    estado = forms.ChoiceField(
        choices=[('', 'Todos los estados')] + Lote.ESTADOS_CHOICES,
        required=False
    )
    fecha_caducidad_desde = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    fecha_caducidad_hasta = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'get'
        self.helper.layout = Layout(
            Row(
                Column('institucion', css_class='form-group col-md-4 mb-0'),
                Column('producto', css_class='form-group col-md-4 mb-0'),
                Column('categoria', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('estado', css_class='form-group col-md-4 mb-0'),
                Column('fecha_caducidad_desde', css_class='form-group col-md-4 mb-0'),
                Column('fecha_caducidad_hasta', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            Submit('submit', 'Filtrar', css_class='btn btn-primary'),
            HTML('<a href="?" class="btn btn-secondary ml-2">Limpiar Filtros</a>')
        )


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'username',
            'email',
            Row(
                Column('first_name', css_class='form-group col-md-6 mb-0'),
                Column('last_name', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            'password1',
            'password2',
            Submit('submit', 'Crear Usuario', css_class='btn btn-primary')
        )

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        if commit:
            user.save()
        return user

# inventario/forms.py
from django import forms

class CargaMasivaInstitucionForm(forms.Form):
    archivo = forms.FileField(label="Archivo Excel (CLUES.xlsx)")


class CargaLotesForm(forms.Form):
    archivo = forms.FileField(
        label="Archivo Excel",
        help_text="Archivo Excel con columnas LOTE y UBICACIÓN",
        widget=forms.FileInput(attrs={'accept': '.xlsx,.xls'})
    )
    institucion = forms.ModelChoiceField(
        queryset=Institucion.objects.filter(activo=True),
        label="Institución",
        help_text="Seleccione la institución para los lotes"
    )


# ============================================================================
# NUEVOS FORMULARIOS PARA FASE 2
# ============================================================================

class CitaProveedorForm(forms.ModelForm):
    """
    Formulario para crear y editar citas con proveedores.
    
    Permite registrar:
    - Proveedor
    - Fecha y hora de la cita
    - Almacén de recepción
    - Observaciones
    """
    
    class Meta:
        model = CitaProveedor
        fields = ['proveedor', 'fecha_cita', 'almacen', 'observaciones']
        widgets = {
            'proveedor': forms.Select(attrs={
                'class': 'form-control form-control-lg',
                'required': True,
                'placeholder': 'Seleccione un proveedor'
            }),
            'fecha_cita': forms.DateTimeInput(attrs={
                'class': 'form-control form-control-lg',
                'type': 'datetime-local',
                'required': True,
                'placeholder': 'Seleccione fecha y hora'
            }),
            'almacen': forms.Select(attrs={
                'class': 'form-control form-control-lg',
                'required': True,
                'placeholder': 'Seleccione almacén'
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Observaciones adicionales sobre la cita (opcional)',
                'maxlength': 500
            }),
        }
        labels = {
            'proveedor': '👥 Proveedor',
            'fecha_cita': '📅 Fecha y Hora de Cita',
            'almacen': '🏢 Almacén de Recepción',
            'observaciones': '📝 Observaciones',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Row(
                Column('proveedor', css_class='form-group col-md-6 mb-3'),
                Column('almacen', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            Row(
                Column('fecha_cita', css_class='form-group col-md-12 mb-3'),
                css_class='form-row'
            ),
            'observaciones',
            HTML('<hr class="my-4">'),
            Submit('submit', '✓ Guardar Cita', css_class='btn btn-primary btn-lg w-100')
        )
    
    def clean(self):
        cleaned_data = super().clean()
        fecha_cita = cleaned_data.get('fecha_cita')
        
        if fecha_cita:
            from django.utils import timezone
            # Validar que la cita sea en el futuro
            ahora = timezone.now()
            if fecha_cita < ahora:
                raise forms.ValidationError(
                    "La fecha y hora de la cita debe ser en el futuro."
                )
        
        return cleaned_data


class OrdenTrasladoForm(forms.ModelForm):
    """
    Formulario para crear órdenes de traslado entre almacenes.
    
    Permite especificar:
    - Almacén origen
    - Almacén destino
    - Ruta (descripción del recorrido)
    
    Validaciones:
    - El almacén origen no puede ser igual al destino
    """
    
    class Meta:
        model = OrdenTraslado
        fields = ['almacen_origen', 'almacen_destino', 'ruta']
        widgets = {
            'almacen_origen': forms.Select(attrs={
                'class': 'form-control form-control-lg',
                'required': True,
                'placeholder': 'Seleccione almacén de origen'
            }),
            'almacen_destino': forms.Select(attrs={
                'class': 'form-control form-control-lg',
                'required': True,
                'placeholder': 'Seleccione almacén de destino'
            }),
            'ruta': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Ruta Centro - Zona Norte',
                'maxlength': 200
            }),
        }
        labels = {
            'almacen_origen': '📤 Almacén Origen',
            'almacen_destino': '📥 Almacén Destino',
            'ruta': '🛣️ Ruta (Descripción)',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Row(
                Column('almacen_origen', css_class='form-group col-md-6 mb-3'),
                Column('almacen_destino', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            'ruta',
            HTML('<hr class="my-4">'),
            Submit('submit', '✓ Crear Orden de Traslado', css_class='btn btn-primary btn-lg w-100')
        )
    
    def clean(self):
        cleaned_data = super().clean()
        origen = cleaned_data.get('almacen_origen')
        destino = cleaned_data.get('almacen_destino')
        
        if origen and destino:
            if origen == destino:
                raise forms.ValidationError(
                    "El almacén de origen y destino no pueden ser iguales. "
                    "Seleccione almacenes diferentes."
                )
        
        return cleaned_data


class LogisticaTrasladoForm(forms.ModelForm):
    """
    Formulario para asignar datos de logística a una orden de traslado.
    
    Permite registrar:
    - Placa del vehículo
    - Nombre del chofer
    - Cédula del chofer
    - Ruta
    
    Este formulario se utiliza después de crear la orden de traslado
    para asignar los detalles de logística (vehículo y chofer).
    """
    
    class Meta:
        model = OrdenTraslado
        fields = ['vehiculo_placa', 'chofer_nombre', 'chofer_cedula', 'ruta']
        widgets = {
            'vehiculo_placa': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Ej: ABC-1234',
                'maxlength': 20,
                'required': True,
                'pattern': '[A-Z]{3}-[0-9]{4}',
                'title': 'Formato: ABC-1234'
            }),
            'chofer_nombre': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Nombre completo del chofer',
                'maxlength': 100,
                'required': True
            }),
            'chofer_cedula': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Ej: 1234567890',
                'maxlength': 20,
                'required': True
            }),
            'ruta': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Descripción de la ruta',
                'maxlength': 200
            }),
        }
        labels = {
            'vehiculo_placa': '🚚 Placa del Vehículo',
            'chofer_nombre': '👤 Nombre del Chofer',
            'chofer_cedula': '🆔 Cédula del Chofer',
            'ruta': '🛣️ Ruta',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Row(
                Column('vehiculo_placa', css_class='form-group col-md-6 mb-3'),
                Column('chofer_cedula', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            'chofer_nombre',
            'ruta',
            HTML('<div class="alert alert-info mt-3">'),
            HTML('<strong>ℹ️ Información:</strong> Los datos de logística son necesarios para rastrear el traslado.'),
            HTML('</div>'),
            HTML('<hr class="my-4">'),
            Submit('submit', '✓ Asignar Logística', css_class='btn btn-success btn-lg w-100')
        )
    
    def clean(self):
        cleaned_data = super().clean()
        placa = cleaned_data.get('vehiculo_placa')
        cedula = cleaned_data.get('chofer_cedula')
        
        # Validar formato de placa (ABC-1234)
        if placa:
            import re
            if not re.match(r'^[A-Z]{3}-[0-9]{4}$', placa):
                raise forms.ValidationError(
                    "La placa debe tener el formato ABC-1234"
                )
        
        # Validar que la cédula sea numérica
        if cedula:
            if not cedula.isdigit():
                raise forms.ValidationError(
                    "La cédula debe contener solo números"
                )
        
        return cleaned_data


<<<<<<< HEAD
class ConteoFisicoForm(forms.ModelForm):
    """Formulario para crear/editar sesiones de conteo físico"""
    class Meta:
        model = ConteoFisico
        fields = ['almacen', 'observaciones']
        widgets = {
            'observaciones': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Row(
                Column('almacen', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            'observaciones',
            Submit('submit', '✓ Crear Conteo', css_class='btn btn-primary')
        )
=======

# ============================================================================
# FASE 2.2.1: FORMULARIOS PARA GESTIÓN DE PEDIDOS Y SALIDA
# ============================================================================

from datetime import date, timedelta
from .models import SolicitudPedido, ItemSolicitudPedido, SalidaExistencias, Almacen


class SolicitudPedidoForm(forms.ModelForm):
    """Formulario para crear una nueva solicitud de pedido"""
    
    class Meta:
        model = SolicitudPedido
        fields = ['institucion', 'almacen_origen', 'fecha_entrega_programada', 'observaciones']
        widgets = {
            'institucion': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'almacen_origen': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'fecha_entrega_programada': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True,
                'min': (date.today() + timedelta(days=1)).isoformat()
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observaciones adicionales (opcional)'
            }),
        }
    
    def __init__(self, *args, institucion=None, **kwargs):
        super().__init__(*args, **kwargs)
        if institucion:
            self.fields['institucion'].initial = institucion
            self.fields['institucion'].queryset = Institucion.objects.filter(id=institucion.id)


class ItemSolicitudPedidoForm(forms.ModelForm):
    """Formulario para agregar items a una solicitud"""
    
    producto = forms.ModelChoiceField(
        queryset=Producto.objects.all(),
        widget=forms.Select(attrs={
            'class': 'form-control',
            'required': True
        }),
        label="Producto (CNIS)"
    )
    
    class Meta:
        model = ItemSolicitudPedido
        fields = ['producto', 'cantidad_solicitada']
        widgets = {
            'cantidad_solicitada': forms.NumberInput(attrs={
                'class': 'form-control',
                'type': 'number',
                'min': '1',
                'required': True
            }),
        }


class ValidarSolicitudPedidoForm(forms.Form):
    """Formulario para validar una solicitud y generar movimiento"""
    
    def __init__(self, *args, solicitud=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.solicitud = solicitud
        
        if solicitud:
            # Crear un campo para cada item de la solicitud
            for item in solicitud.items.all():
                field_name = f'item_{item.id}_cantidad'
                self.fields[field_name] = forms.IntegerField(
                    label=f"{item.producto.clave_cnis} - {item.producto.descripcion}",
                    initial=item.cantidad_solicitada,
                    min_value=0,
                    max_value=item.cantidad_solicitada,
                    widget=forms.NumberInput(attrs={
                        'class': 'form-control',
                        'type': 'number'
                    })
                )
                
                # Campo para seleccionar lote (FIFO)
                lote_field_name = f'item_{item.id}_lote'
                available_lotes = Lote.objects.filter(
                    producto=item.producto,
                    cantidad_disponible__gt=0
                ).order_by('fecha_caducidad')
                
                self.fields[lote_field_name] = forms.ModelChoiceField(
                    queryset=available_lotes,
                    required=False,
                    label=f"Lote para {item.producto.clave_cnis}",
                    widget=forms.Select(attrs={
                        'class': 'form-control'
                    })
                )


class ConfirmarSalidaForm(forms.Form):
    """Formulario para confirmar salida de existencias"""
    
    nombre_receptor = forms.CharField(
        max_length=200,
        label="Nombre del Receptor",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'required': True
        })
    )
    
    firma_receptor = forms.CharField(
        label="Firma Digital (Canvas)",
        widget=forms.HiddenInput(),
        required=False
    )
    
    observaciones = forms.CharField(
        label="Observaciones",
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Observaciones adicionales (opcional)'
        })
    )


class FiltroSolicitudesForm(forms.Form):
    """Formulario para filtrar solicitudes de pedidos"""
    
    ESTADO_CHOICES = [('', 'Todos los estados')] + SolicitudPedido.ESTADO_CHOICES
    
    estado = forms.ChoiceField(
        choices=ESTADO_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    institucion = forms.ModelChoiceField(
        queryset=Institucion.objects.all(),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    fecha_desde = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    fecha_hasta = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    buscar = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por folio...'
        })
    )
>>>>>>> 7195864190c6300af481c27e7bf7647063d399ca
