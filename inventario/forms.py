
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
    CitaProveedor, OrdenTraslado, ItemTraslado, ConteoFisico, ItemConteoFisico, TipoRed, TipoEntrega,
    Almacen
)
#from .models import Institucion, Alcaldia, TipoInstitucion


class InstitucionForm(forms.ModelForm):
    class Meta:
        model = Institucion
        fields = ["clue", "ib_clue", "denominacion", "alcaldia", "tipo_institucion", 
                 "direccion", "telefono", "email", "activo"]
        widgets = {
            "direccion": forms.Textarea(attrs={"rows": 3}),
            "clue": forms.TextInput(attrs={"placeholder": "Ej: DFIMB002324"}),
            "ib_clue": forms.TextInput(attrs={"placeholder": "Ej: DFIMB002324"}),
            "denominacion": forms.TextInput(attrs={"placeholder": "Nombre completo de la institución"}),
            "telefono": forms.TextInput(attrs={"placeholder": "55-1234-5678"}),
            "email": forms.EmailInput(attrs={"placeholder": "contacto@institucion.gob.mx"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column("clue", css_class="form-group col-md-6 mb-0"),
                Column("ib_clue", css_class="form-group col-md-6 mb-0"),
                css_class="form-row"
            ),
            "denominacion",
            Row(
                Column("alcaldia", css_class="form-group col-md-6 mb-0"),
                Column("tipo_institucion", css_class="form-group col-md-6 mb-0"),
                css_class="form-row"
            ),
            "direccion",
            Row(
                Column("telefono", css_class="form-group col-md-6 mb-0"),
                Column("email", css_class="form-group col-md-6 mb-0"),
                css_class="form-row"
            ),
            "activo",
            Submit("submit", "Guardar Institución", css_class="btn btn-primary")
        )


# forms.py
class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = [
            "clave_cnis",
            "descripcion",
            "categoria",
            "unidad_medida",
            "es_insumo_cpm",
            "precio_unitario_referencia",
            "clave_saica",
            "descripcion_saica",
            "unidad_medida_saica",
            "proveedor",
            "rfc_proveedor",
            "partida_presupuestal",
            "marca",
            "fabricante",
            "cantidad_disponible",
            "activo"
        ]
        widgets = {
            "descripcion": forms.Textarea(attrs={"rows": 3}),
            "descripcion_saica": forms.Textarea(attrs={"rows": 2}),
            "clave_cnis": forms.TextInput(attrs={"placeholder": "Ej: 010.000.0022.00"}),
            "clave_saica": forms.TextInput(attrs={"placeholder": "Ej: 1234-SAICA"}),
            "precio_unitario_referencia": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "cantidad_disponible": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "unidad_medida": forms.TextInput(attrs={"placeholder": "Ej: PIEZA"}),
            "unidad_medida_saica": forms.TextInput(attrs={"placeholder": "Ej: CAJA, LITRO, etc."}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Row(
                Column("clave_cnis", css_class="form-group col-md-6 mb-0"),
                Column("categoria", css_class="form-group col-md-6 mb-0"),
                css_class="form-row"
            ),
            "descripcion",
            Row(
                Column("unidad_medida", css_class="form-group col-md-4 mb-0"),
                Column("precio_unitario_referencia", css_class="form-group col-md-4 mb-0"),
                Column(
                    Div(
                        "es_insumo_cpm",
                        "activo",
                        css_class="mt-3"
                    ),
                    css_class="form-group col-md-4 mb-0"
                ),
                css_class="form-row"
            ),
            HTML("<hr><h5>Datos complementarios</h5>"),
            Row(
                Column("clave_saica", css_class="form-group col-md-6 mb-0"),
                Column("descripcion_saica", css_class="form-group col-md-6 mb-0"),
                css_class="form-row"
            ),
            Row(
                Column("unidad_medida_saica", css_class="form-group col-md-4 mb-0"),
                Column("proveedor", css_class="form-group col-md-4 mb-0"),
                Column("rfc_proveedor", css_class="form-group col-md-4 mb-0"),
                css_class="form-row"
            ),
            Row(
                Column("partida_presupuestal", css_class="form-group col-md-4 mb-0"),
                Column("marca", css_class="form-group col-md-4 mb-0"),
                Column("fabricante", css_class="form-group col-md-4 mb-0"),
                css_class="form-row"
            ),
            Row(
                Column("cantidad_disponible", css_class="form-group col-md-6 mb-0"),
                css_class="form-row"
            ),
            Submit("submit", "Guardar Producto", css_class="btn btn-primary")
        )




class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = ["rfc", "razon_social", "direccion", "telefono", "email", 
                 "contacto_principal", "activo"]
        widgets = {
            "direccion": forms.Textarea(attrs={"rows": 3}),
            "rfc": forms.TextInput(attrs={"placeholder": "Ej: ABC123456789"}),
            "razon_social": forms.TextInput(attrs={"placeholder": "Nombre de la empresa"}),
            "telefono": forms.TextInput(attrs={"placeholder": "55-1234-5678"}),
            "email": forms.EmailInput(attrs={"placeholder": "contacto@proveedor.com"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column("rfc", css_class="form-group col-md-6 mb-0"),
                Column("razon_social", css_class="form-group col-md-6 mb-0"),
                css_class="form-row"
            ),
            "direccion",
            Row(
                Column("telefono", css_class="form-group col-md-4 mb-0"),
                Column("email", css_class="form-group col-md-4 mb-0"),
                Column("contacto_principal", css_class="form-group col-md-4 mb-0"),
                css_class="form-row"
            ),
            "activo",
            Submit("submit", "Guardar Proveedor", css_class="btn btn-primary")
        )


class LoteForm(forms.ModelForm):
    class Meta:
        model = Lote
        exclude = ["uuid", "fecha_creacion", "fecha_actualizacion", "creado_por",
                   "fecha_cambio_estado", "usuario_cambio_estado", "valor_total"]
        widgets = {
            "fecha_fabricacion": forms.DateInput(
                attrs={"type": "date"},
                format="%Y-%m-%d"
            ),
            "fecha_caducidad": forms.DateInput(
                attrs={"type": "date"}, 
                format="%Y-%m-%d"
            ),
            "fecha_recepcion": forms.DateInput(
                attrs={"type": "date"},
                format="%Y-%m-%d"
            ),
            "fecha_fabricacion_csv": forms.DateInput(
                attrs={"type": "date"},
                format="%Y-%m-%d"
            ),
            "precio_unitario": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "cantidad_inicial": forms.NumberInput(attrs={"min": "1"}),
            "cantidad_disponible": forms.NumberInput(attrs={"min": "0"}),
            "observaciones": forms.Textarea(attrs={"rows": 3}),
            "motivo_cambio_estado": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Establecer formatos de entrada para campos de fecha
        date_fields = ["fecha_fabricacion", "fecha_caducidad", "fecha_recepcion", "fecha_fabricacion_csv"]
        for field_name in date_fields:
            self.fields[field_name].input_formats = ["%Y-%m-%d"]  # Formato YYYY-MM-DD
            
            # Si hay una instancia con fechas, formatearlas correctamente para el widget
            if self.instance and getattr(self.instance, field_name):
                try:
                    self.initial[field_name] = getattr(self.instance, field_name).strftime("%Y-%m-%d")
                except (AttributeError, ValueError):
                    # Si hay algún error, mantener el valor actual
                    pass

        # Filtrado dinámico de ubicaciones según el almacén
        if "almacen" in self.data:
            try:
                almacen_id = int(self.data.get("almacen"))
                self.fields["ubicacion"].queryset = UbicacionAlmacen.objects.filter(
                    almacen_id=almacen_id,
                    activo=True
                ).order_by("codigo")
            except (ValueError, TypeError):
                self.fields["ubicacion"].queryset = UbicacionAlmacen.objects.none()
        elif self.instance.pk and self.instance.almacen:
            self.fields["ubicacion"].queryset = UbicacionAlmacen.objects.filter(
                almacen=self.instance.almacen,
                activo=True
            ).order_by("codigo")
        else:
            self.fields["ubicacion"].queryset = UbicacionAlmacen.objects.none()

        self.helper = FormHelper()
        self.helper.layout = Layout(
            HTML("<h5 class=\"mt-3 text-primary\">Información General</h5>"),
            Row(
                Column("numero_lote", css_class="col-md-3"),
                Column("producto", css_class="col-md-3"),
                Column("institucion", css_class="col-md-3"),
                Column("almacen", css_class="col-md-3"),
            ),
            HTML("<h5 class=\"mt-3 text-primary\">Cantidades y Precios</h5>"),
            Row(
                Column("cantidad_inicial", css_class="col-md-3"),
                Column("cantidad_disponible", css_class="col-md-3"),
                Column("precio_unitario", css_class="col-md-3"),
            ),
            HTML("<h5 class=\"mt-3 text-primary\">Fechas</h5>"),
            Row(
                Column("fecha_fabricacion", css_class="col-md-3"),
                Column("fecha_caducidad", css_class="col-md-3"),
                Column("fecha_recepcion", css_class="col-md-3"),
            ),
            HTML("<h5 class=\"mt-3 text-primary\">Ubicación</h5>"),
            Row(
                Column("ubicacion", css_class="col-md-6"),
            ),
            HTML("<h5 class=\"mt-3 text-primary\">Otros</h5>"),
            "observaciones",
            "estado",
            "motivo_cambio_estado",
            Submit("submit", "Guardar Lote", css_class="btn btn-primary mt-3")
        )

    def clean(self):
        cleaned_data = super().clean()
        cantidad_inicial = cleaned_data.get("cantidad_inicial")
        cantidad_disponible = cleaned_data.get("cantidad_disponible")
        fecha_fabricacion = cleaned_data.get("fecha_fabricacion")
        fecha_caducidad = cleaned_data.get("fecha_caducidad")

        if cantidad_inicial and cantidad_inicial < 0:
            self.add_error("cantidad_inicial", "La cantidad inicial no puede ser negativa.")

        if cantidad_disponible and cantidad_disponible < 0:
            self.add_error("cantidad_disponible", "La cantidad disponible no puede ser negativa.")

        if fecha_fabricacion and fecha_caducidad and fecha_fabricacion > fecha_caducidad:
            self.add_error("fecha_caducidad", "La fecha de caducidad no puede ser anterior a la de fabricación.")

        return cleaned_data


class MovimientoInventarioForm(forms.ModelForm):
    class Meta:
        model = MovimientoInventario
        fields = ["lote", "tipo_movimiento", "cantidad", "motivo"]
        widgets = {
            "motivo": forms.Textarea(attrs={"rows": 3}),
        }


class CargaInventarioForm(forms.ModelForm):
    class Meta:
        model = CargaInventario
        fields = ["archivo", "nombre_archivo"]
        widgets = {
            "archivo": forms.FileInput(attrs={"accept": ".xlsx,.xls"}),
            "nombre_archivo": forms.TextInput(attrs={"placeholder": "Nombre del archivo"}),
        }


class FiltroInventarioForm(forms.Form):
    search = forms.CharField(required=False, label="Buscar por Lote o Producto")
    institucion = forms.ModelChoiceField(queryset=Institucion.objects.all(), required=False)
    almacen = forms.ModelChoiceField(queryset=Almacen.objects.all(), required=False)
    categoria = forms.ModelChoiceField(queryset=CategoriaProducto.objects.all(), required=False)
    estado = forms.ChoiceField(choices=[("", "Todos")] + Lote.ESTADOS, required=False)


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ("first_name", "last_name", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            "username",
            "first_name",
            "last_name",
            "email",
            "password",
            "password2",
            Submit("submit", "Crear Usuario", css_class="btn btn-primary")
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
        widget=forms.FileInput(attrs={"accept": ".xlsx,.xls"})
    )
    institucion = forms.ModelChoiceField(
        queryset=Institucion.objects.filter(activo=True),
        label="Institución",
        help_text="Seleccione la institución para los lotes"
    )


# ============================================================================
# NUEVOS FORMULARIOS PARA FASE 2
# ============================================================================
from django.utils import timezone
from datetime import timedelta

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
        fields = ["proveedor", "fecha_cita", "almacen", "observaciones"]
        widgets = {
            "proveedor": forms.Select(attrs={
                "class": "form-control form-control-lg",
                "required": True,
                "placeholder": "Seleccione un proveedor"
            }),
            "fecha_cita": forms.DateTimeInput(attrs={
                "class": "form-control form-control-lg",
                "type": "datetime-local",
                "required": True,
                "placeholder": "Seleccione fecha y hora"
            }),
            "almacen": forms.Select(attrs={
                "class": "form-control form-control-lg",
                "required": True,
                "placeholder": "Seleccione almacén"
            }),
            "observaciones": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Observaciones adicionales sobre la cita (opcional)",
                "maxlength": 500
            }),
        }
        labels = {
            "proveedor": "👥 Proveedor",
            "fecha_cita": "📅 Fecha y Hora de Cita",
            "almacen": "🏢 Almacén de Recepción",
            "observaciones": "📝 Observaciones",
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.layout = Layout(
            Row(
                Column("proveedor", css_class="form-group col-md-6 mb-3"),
                Column("almacen", css_class="form-group col-md-6 mb-3"),
                css_class="form-row"
            ),
            Row(
                Column("fecha_cita", css_class="form-group col-md-12 mb-3"),
                css_class="form-row"
            ),
            "observaciones",
            HTML("<hr class=\"my-4\">"),
            Submit("submit", "✓ Guardar Cita", css_class="btn btn-primary btn-lg w-100")
        )
    
    def clean_fecha_cita(self):
        fecha_cita = self.cleaned_data.get("fecha_cita")
        if not fecha_cita:
            return fecha_cita
        # Permitir fechas pasadas solo durante los próximos 3 días
        ahora = timezone.now()
        if ahora > fecha_cita:
            diferencia_dias = (ahora - fecha_cita).days
            if diferencia_dias > 3:
                raise forms.ValidationError("La fecha de la cita no puede ser en el pasado.")
        return fecha_cita

    def clean(self):
        cleaned_data = super().clean()
        fecha_cita = cleaned_data.get("fecha_cita")
        
        if fecha_cita:
            # La validación de fechas pasadas se hace en clean_fecha_cita
            pass

        return cleaned_data


class OrdenTrasladoForm(forms.ModelForm):
    """
    Formulario para crear y editar órdenes de traslado.
    """
    class Meta:
        model = OrdenTraslado
        fields = ["almacen_origen", "almacen_destino", "fecha_estimada_salida", "fecha_estimada_llegada", "observaciones"]
        widgets = {
            "fecha_estimada_salida": forms.DateInput(attrs={"type": "date"}),
            "fecha_estimada_llegada": forms.DateInput(attrs={"type": "date"}),
            "observaciones": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.layout = Layout(
            Row(
                Column("almacen_origen", css_class="form-group col-md-6 mb-3"),
                Column("almacen_destino", css_class="form-group col-md-6 mb-3"),
                css_class="form-row"
            ),
            Row(
                Column("fecha_estimada_salida", css_class="form-group col-md-6 mb-3"),
                Column("fecha_estimada_llegada", css_class="form-group col-md-6 mb-3"),
                css_class="form-row"
            ),
            "observaciones",
            HTML("<hr class=\"my-4\">"),
            Submit("submit", "✓ Crear Orden de Traslado", css_class="btn btn-primary btn-lg w-100")
        )
    
    def clean(self):
        cleaned_data = super().clean()
        origen = cleaned_data.get("almacen_origen")
        destino = cleaned_data.get("almacen_destino")
        
        if origen and destino and origen == destino:
            raise forms.ValidationError("El almacén de origen y destino no pueden ser el mismo.")
        
        return cleaned_data


class LogisticaTrasladoForm(forms.ModelForm):
    """
    Formulario para asignar detalles de logística a una orden de traslado.
    """
    class Meta:
        model = OrdenTraslado
        fields = ["vehiculo_placa", "vehiculo_descripcion", "chofer_nombre", "chofer_cedula", "ruta_descripcion"]
        widgets = {
            "ruta_descripcion": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.layout = Layout(
            Row(
                Column("vehiculo_placa", css_class="form-group col-md-6 mb-3"),
                Column("vehiculo_descripcion", css_class="form-group col-md-6 mb-3"),
                css_class="form-row"
            ),
            Row(
                Column("chofer_nombre", css_class="form-group col-md-6 mb-3"),
                Column("chofer_cedula", css_class="form-group col-md-6 mb-3"),
                css_class="form-row"
            ),
            "ruta_descripcion",
            HTML("<hr class=\"my-4\">"),
            Submit("submit", "✓ Asignar Logística", css_class="btn btn-success btn-lg w-100")
        )
    
    def clean(self):
        cleaned_data = super().clean()
        placa = cleaned_data.get("vehiculo_placa")
        cedula = cleaned_data.get("chofer_cedula")
        
        # Aquí podrías añadir validaciones de formato para placa y cédula si es necesario
        
        return cleaned_data


class ItemTrasladoForm(forms.ModelForm):
    """
    Formulario para añadir o editar items en una orden de traslado.
    """
    class Meta:
        model = ItemTraslado
        fields = ["lote", "cantidad"]
        widgets = {
            "lote": ModelSelect2Widget(
                model=Lote,
                search_fields=["numero_lote__icontains", "producto__descripcion__icontains"],
                attrs={"data-placeholder": "Busca un lote..."}
            )
        }

    def __init__(self, *args, **kwargs):
        almacen_origen = kwargs.pop("almacen_origen", None)
        super().__init__(*args, **kwargs)
        
        if almacen_origen:
            self.fields["lote"].queryset = Lote.objects.filter(
                institucion__almacen=almacen_origen,
                cantidad_disponible__gt=0,
                estado=1
            ).order_by("-fecha_recepcion")
    
    def clean(self):
        cleaned_data = super().clean()
        lote = cleaned_data.get("lote")
        cantidad = cleaned_data.get("cantidad")
        
        if lote and cantidad:
            if cantidad > lote.cantidad_disponible:
                raise forms.ValidationError(f"La cantidad solicitada ({cantidad}) supera la disponible ({lote.cantidad_disponible}).")
        
        return cleaned_data


class ItemConteoFisicoForm(forms.ModelForm):
    """
    Formulario para registrar un item en un conteo físico.
    """
    class Meta:
        model = ItemConteoFisico
        fields = ["lote", "cantidad_fisica", "observaciones"]
        widgets = {
            "lote": forms.Select(attrs={
                "class": "form-control",
                "required": True
            }),
            "cantidad_fisica": forms.NumberInput(attrs={
                "class": "form-control",
                "required": True,
                "min": 0
            }),
            "observaciones": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 2
            }),
        }
