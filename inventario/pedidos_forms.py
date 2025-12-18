'''
Formularios para el módulo de Gestión de Pedidos (Fase 2.2.1)
'''

from django import forms
from django.forms import inlineformset_factory
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, HTML
from datetime import date, timedelta
from django_select2.forms import ModelSelect2Widget

from .pedidos_models import SolicitudPedido, ItemSolicitud
from .models import Producto, Lote, Institucion, Almacen


class SolicitudPedidoForm(forms.ModelForm):
    """
    Formulario para crear una nueva solicitud de pedido con Select2.
    """
    
    institucion_solicitante = forms.ModelChoiceField(
        queryset=Institucion.objects.all(),
        widget=ModelSelect2Widget(
            model=Institucion,
            search_fields=['nombre__icontains'],
            attrs={
                'class': 'form-control',
                'data-placeholder': 'Selecciona una institución',
                'style': 'width: 100%'
            }
        ),
        label="Institución Solicitante"
    )
    
    almacen_destino = forms.ModelChoiceField(
        queryset=Almacen.objects.all(),
        widget=ModelSelect2Widget(
            model=Almacen,
            search_fields=['nombre__icontains'],
            attrs={
                'class': 'form-control',
                'data-placeholder': 'Selecciona un almacén',
                'style': 'width: 100%'
            }
        ),
        label="Almacén Destino"
    )
    
    class Meta:
        model = SolicitudPedido
        fields = [
            'institucion_solicitante',
            'almacen_destino',
            'fecha_entrega_programada',
            'observaciones_solicitud'
        ]
        widgets = {
            'fecha_entrega_programada': forms.DateInput(
                attrs={
                    'class': 'form-control',
                    'type': 'date',
                    'min': (date.today() + timedelta(days=1)).isoformat()
                }
            ),
            'observaciones_solicitud': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 3,
                    'placeholder': 'Observaciones adicionales (opcional)'
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
    Formulario para agregar items a una solicitud de pedido con Select2.
    """
    
    producto = forms.ModelChoiceField(
        queryset=Producto.objects.filter(activo=True),
        widget=ModelSelect2Widget(
            model=Producto,
            search_fields=['clave_cnis__icontains', 'descripcion__icontains'],
            attrs={
                'class': 'form-control',
                'data-placeholder': 'Busca por CNIS o descripción',
                'style': 'width: 100%'
            }
        ),
        label="Producto (CNIS)"
    )
    
    class Meta:
        model = ItemSolicitud
        fields = ['producto', 'cantidad_solicitada']
        widgets = {
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


# Formset para editar múltiples items en una solicitud
ItemSolicitudFormSet = inlineformset_factory(
    SolicitudPedido,
    ItemSolicitud,
    form=ItemSolicitudForm,
    extra=3,
    can_delete=True
)
