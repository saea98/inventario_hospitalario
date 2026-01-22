'''
Formularios para el módulo de Gestión de Pedidos (Fase 2.2.1)
'''

from django import forms
from django.forms import inlineformset_factory
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, HTML
from datetime import date, timedelta

from .pedidos_models import SolicitudPedido, ItemSolicitud, PropuestaPedido, ItemPropuesta
from .models import Producto, Lote, Institucion, Almacen


class SolicitudPedidoForm(forms.ModelForm):
    """
    Formulario para crear una nueva solicitud de pedido.
    """
    
    class Meta:
        model = SolicitudPedido
        fields = [
            'institucion_solicitante',
            'almacen_destino',
            'fecha_entrega_programada',
            'observaciones_solicitud'
        ]
        widgets = {
            'institucion_solicitante': forms.Select(attrs={
                'class': 'form-control select2-single',
                'data-placeholder': 'Selecciona una institución',
                'required': 'required'
            }),
            'almacen_destino': forms.Select(attrs={
                'class': 'form-control select2-single',
                'data-placeholder': 'Selecciona un almacén',
                'required': 'required'
            }),
            'fecha_entrega_programada': forms.DateInput(
                attrs={
                    'class': 'form-control',
                    'type': 'date',
                    'min': date.today().isoformat(),
                    'required': 'required'
                }
            ),
            'observaciones_solicitud': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Folio del Pedido (opcional)',
                    'type': 'text'
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Asegurar que los campos requeridos estén marcados
        self.fields['institucion_solicitante'].required = True
        self.fields['almacen_destino'].required = True
        self.fields['fecha_entrega_programada'].required = True
        
        # Filtrar almacenes por institucion si esta seleccionada
        if self.instance.pk:
            try:
                if self.instance.institucion_solicitante:
                    self.fields['almacen_destino'].queryset = Almacen.objects.filter(
                        institucion=self.instance.institucion_solicitante
                    ).order_by('nombre')
                else:
                    self.fields['almacen_destino'].queryset = Almacen.objects.all().order_by('nombre')
            except:
                self.fields['almacen_destino'].queryset = Almacen.objects.all().order_by('nombre')
        else:
            # Mostrar todos los almacenes si no hay institucion seleccionada
            self.fields['almacen_destino'].queryset = Almacen.objects.all().order_by('nombre')
        
        # Agregar data-attribute para filtrado dinámico con JavaScript
        self.fields['institucion_solicitante'].widget.attrs['data-almacen-filter'] = 'true'
        self.fields['almacen_destino'].widget.attrs['data-filtered-select'] = 'true'
        
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('institucion_solicitante', css_class='form-group col-md-6 mb-0'),
                Column('almacen_destino', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            'fecha_entrega_programada',
            'observaciones_solicitud',
            Submit('submit', 'Crear Solicitud', css_class='btn btn-primary')
        )


class ItemSolicitudForm(forms.ModelForm):
    """
    Formulario para agregar items a una solicitud de pedido.
    """
    
    class Meta:
        model = ItemSolicitud
        fields = ['producto', 'cantidad_solicitada']
        widgets = {
            'producto': forms.Select(attrs={
                'class': 'form-control select2-single',
                'data-placeholder': 'Busca por CNIS o descripción'
            }),
            'cantidad_solicitada': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'type': 'number',
                    'min': '1',
                    'required': True
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar solo productos activos
        self.fields['producto'].queryset = Producto.objects.filter(activo=True)
        
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Row(
                Column('producto', css_class='form-group col-md-8 mb-0'),
                Column('cantidad_solicitada', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
        )


class ValidarSolicitudPedidoForm(forms.Form):
    """
    Formulario dinámico para validar una solicitud de pedido.
    Permite aprobar o rechazar cada item con cantidad aprobada.
    """
    
    def __init__(self, *args, solicitud=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.solicitud = solicitud
        
        if solicitud:
            # Crear un campo para cada item de la solicitud
            for item in solicitud.items.all():
                # Campo para cantidad aprobada
                field_name = f'item_{item.id}_cantidad_aprobada'
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
                
                # Campo para justificación si hay cambios
                justif_field_name = f'item_{item.id}_justificacion'
                self.fields[justif_field_name] = forms.CharField(
                    label=f"Justificación (si aplica)",
                    required=False,
                    widget=forms.Textarea(attrs={
                        'class': 'form-control',
                        'rows': 2,
                        'placeholder': 'Ej: No hay disponibilidad, se reduce cantidad, etc.'
                    })
                )

    def clean(self):
        cleaned_data = super().clean()
        
        if self.solicitud:
            for item in self.solicitud.items.all():
                field_name = f'item_{item.id}_cantidad_aprobada'
                cantidad_aprobada = cleaned_data.get(field_name)
                
                if cantidad_aprobada is not None and cantidad_aprobada < 0:
                    self.add_error(field_name, "La cantidad aprobada no puede ser negativa.")
        
        return cleaned_data


class EditarPropuestaForm(forms.Form):
    """
    Formulario para que el personal de almacén edite la propuesta de pedido.
    Permite cambiar cantidades propuestas y agregar observaciones.
    """
    
    def __init__(self, *args, propuesta=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.propuesta = propuesta
        
        if propuesta:
            # Crear campos para cada item de la propuesta
            for item in propuesta.items.all():
                # Campo para cantidad propuesta
                field_name = f'item_{item.id}_cantidad_propuesta'
                self.fields[field_name] = forms.IntegerField(
                    label=f"{item.producto.clave_cnis} - Cantidad Propuesta",
                    initial=item.cantidad_propuesta,
                    min_value=0,
                    max_value=item.cantidad_disponible,
                    widget=forms.NumberInput(attrs={
                        'class': 'form-control',
                        'type': 'number'
                    })
                )
                
                # Campo para observaciones
                obs_field_name = f'item_{item.id}_observaciones'
                self.fields[obs_field_name] = forms.CharField(
                    label=f"Observaciones",
                    required=False,
                    widget=forms.Textarea(attrs={
                        'class': 'form-control',
                        'rows': 2,
                        'placeholder': 'Observaciones sobre este item'
                    })
                )

    def clean(self):
        cleaned_data = super().clean()
        
        if self.propuesta:
            for item in self.propuesta.items.all():
                field_name = f'item_{item.id}_cantidad_propuesta'
                cantidad = cleaned_data.get(field_name)
                
                if cantidad is not None and cantidad < 0:
                    self.add_error(field_name, "La cantidad no puede ser negativa.")
        
        return cleaned_data


class FiltroSolicitudesForm(forms.Form):
    """
    Formulario para filtrar solicitudes de pedidos por estado y fecha.
    """
    
    ESTADO_CHOICES = [
        ('', 'Todos los estados'),
        ('PENDIENTE', 'Pendiente de Validación'),
        ('VALIDADA', 'Validada y Aprobada'),
        ('RECHAZADA', 'Rechazada'),
        ('EN_PREPARACION', 'En Preparación'),
        ('PREPARADA', 'Preparada para Entrega'),
        ('ENTREGADA', 'Entregada'),
        ('CANCELADA', 'Cancelada'),
    ]
    
    estado = forms.ChoiceField(
        choices=ESTADO_CHOICES,
        required=False,
        label="Estado",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    fecha_inicio = forms.DateField(
        required=False,
        label="Desde",
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    fecha_fin = forms.DateField(
        required=False,
        label="Hasta",
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    institucion = forms.CharField(
        required=False,
        label="Institución",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por nombre de institución'
        })
    )
    
    folio = forms.CharField(
        required=False,
        label="Folio",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por folio (observaciones)'
        })
    )


# Formset para editar múltiples items en una solicitud
ItemSolicitudFormSet = inlineformset_factory(
    SolicitudPedido,
    ItemSolicitud,
    form=ItemSolicitudForm,
    extra=3,
    can_delete=True
)

class BulkUploadForm(forms.Form):
    csv_file = forms.FileField(label='Archivo CSV para carga masiva')
