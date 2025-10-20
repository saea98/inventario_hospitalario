from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Div, HTML
from crispy_forms.bootstrap import Field
from .models import (
    Institucion, Producto, Proveedor, Lote, OrdenSuministro,
    CategoriaProducto, Alcaldia, TipoInstitucion, FuenteFinanciamiento,
    MovimientoInventario, CargaInventario, TipoInstitucion, UbicacionAlmacen
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
            'fecha_fabricacion': forms.DateInput(attrs={'type': 'date'}),
            'fecha_caducidad': forms.DateInput(attrs={'type': 'date'}),
            'fecha_recepcion': forms.DateInput(attrs={'type': 'date'}),
            'fecha_fabricacion_csv': forms.DateInput(attrs={'type': 'date'}),
            'precio_unitario': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'cantidad_inicial': forms.NumberInput(attrs={'min': '1'}),
            'cantidad_disponible': forms.NumberInput(attrs={'min': '0'}),
            'observaciones': forms.Textarea(attrs={'rows': 3}),
            'motivo_cambio_estado': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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
                Column('almacen', css_class='col-md-3')  # Agregamos el almacén
            ),
            Row(
                Column('ubicacion', css_class='col-md-4'),  # Campo ubicación dinámico
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



class MovimientoInventarioForm(forms.ModelForm):
    class Meta:
        model = MovimientoInventario
        fields = ['lote', 'tipo_movimiento', 'cantidad', 'motivo', 
                 'documento_referencia', 'institucion_destino']
        widgets = {
            'motivo': forms.Textarea(attrs={'rows': 3}),
            'cantidad': forms.NumberInput(attrs={'min': '1'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
