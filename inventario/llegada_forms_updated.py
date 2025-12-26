"""
Formularios actualizados para manejar el split de lotes en múltiples ubicaciones.
"""

from django import forms
from django.forms import inlineformset_factory, BaseFormSet
from .llegada_models import LlegadaProveedor, ItemLlegada, DocumentoLlegada


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
