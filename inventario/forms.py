from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Div, HTML
from crispy_forms.bootstrap import Field
from .models import (
    Institucion, Producto, Proveedor, Lote, OrdenSuministro,
    CategoriaProducto, Alcaldia, TipoInstitucion, FuenteFinanciamiento,
    MovimientoInventario, CargaInventario, TipoInstitucion
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


class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['clave_cnis', 'descripcion', 'categoria', 'unidad_medida', 
                 'es_insumo_cpm', 'precio_unitario_referencia', 'activo']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
            'clave_cnis': forms.TextInput(attrs={'placeholder': 'Ej: 010.000.0022.00'}),
            'precio_unitario_referencia': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
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
        fields = ['numero_lote', 'producto', 'institucion', 'orden_suministro',
                 'cantidad_inicial', 'cantidad_disponible', 'precio_unitario',
                 'fecha_fabricacion', 'fecha_caducidad', 'fecha_recepcion', 'estado', 'observaciones']
        widgets = {
            'fecha_fabricacion': forms.DateInput(attrs={'type': 'date'}),
            'fecha_caducidad': forms.DateInput(attrs={'type': 'date'}),
            'fecha_recepcion': forms.DateInput(attrs={'type': 'date'}),
            'precio_unitario': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'cantidad_inicial': forms.NumberInput(attrs={'min': '1'}),
            'cantidad_disponible': forms.NumberInput(attrs={'min': '0'}),
            'observaciones': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('numero_lote', css_class='form-group col-md-6 mb-0'),
                Column('producto', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('institucion', css_class='form-group col-md-6 mb-0'),
                Column('orden_suministro', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('cantidad_inicial', css_class='form-group col-md-4 mb-0'),
                Column('cantidad_disponible', css_class='form-group col-md-4 mb-0'),
                Column('precio_unitario', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('fecha_fabricacion', css_class='form-group col-md-4 mb-0'),
                Column('fecha_caducidad', css_class='form-group col-md-4 mb-0'),
                Column('fecha_recepcion', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            'estado',
            'observaciones',  # <-- agregado
            Submit('submit', 'Guardar Lote', css_class='btn btn-primary')
        )

    def clean(self):
        cleaned_data = super().clean()
        cantidad_inicial = cleaned_data.get('cantidad_inicial')
        cantidad_disponible = cleaned_data.get('cantidad_disponible')
        fecha_fabricacion = cleaned_data.get('fecha_fabricacion')
        fecha_caducidad = cleaned_data.get('fecha_caducidad')

        if cantidad_inicial and cantidad_disponible:
            if cantidad_disponible > cantidad_inicial:
                raise forms.ValidationError(
                    'La cantidad disponible no puede ser mayor a la cantidad inicial.'
                )

        if fecha_fabricacion and fecha_caducidad:
            if fecha_fabricacion >= fecha_caducidad:
                raise forms.ValidationError(
                    'La fecha de fabricación debe ser anterior a la fecha de caducidad.'
                )

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
