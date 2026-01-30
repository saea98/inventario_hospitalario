from django import forms
from django.core.exceptions import ValidationError


class CargaMasivaLotesForm(forms.Form):
    """Formulario para carga masiva de lotes desde Excel"""
    
    archivo = forms.FileField(
        label='Archivo Excel',
        help_text='Formato: .xlsx o .xls',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.xlsx,.xls',
            'id': 'archivo_input'
        })
    )
    
    institucion = forms.IntegerField(
        label='Institución',
        initial=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1'
        })
    )
    
    dry_run = forms.BooleanField(
        label='Modo Previsualización (Dry-Run)',
        required=False,
        initial=False,
        help_text='Si está marcado, muestra cambios sin aplicarlos',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'dry_run_check'
        })
    )
    
    actualizar_cantidad = forms.BooleanField(
        label='Actualizar Cantidades',
        required=False,
        initial=True,
        help_text='Si está marcado, actualiza las cantidades de los lotes. Si no está marcado, solo actualiza otros campos (ubicaciones, fechas, etc.)',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'actualizar_cantidad_check'
        })
    )
    
    def clean_archivo(self):
        archivo = self.cleaned_data.get('archivo')
        
        if not archivo:
            raise ValidationError('Debes seleccionar un archivo')
        
        # Validar extensión
        nombre_archivo = archivo.name.lower()
        if not (nombre_archivo.endswith('.xlsx') or nombre_archivo.endswith('.xls')):
            raise ValidationError('El archivo debe ser Excel (.xlsx o .xls)')
        
        # Validar tamaño (máximo 10MB)
        if archivo.size > 10 * 1024 * 1024:
            raise ValidationError('El archivo no debe exceder 10MB')
        
        return archivo


class CargaMasivaOrdenesSuministroForm(forms.Form):
    """Formulario para carga masiva de órdenes de suministro desde Excel."""

    archivo = forms.FileField(
        label='Archivo Excel',
        help_text='Formato: .xlsx o .xls. Columnas: CLUES, ORDEN DE SUMINISTRO, RFC, CLAVE, LOTE, F_REC. Opcionales: F_FAB, F_CAD.',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.xlsx,.xls',
            'id': 'archivo_ordenes_input'
        })
    )

    partida_default = forms.CharField(
        label='Partida presupuestal por defecto',
        max_length=20,
        required=False,
        initial='N/A',
        help_text='Se usa cuando el producto no tiene partida (max 20 caracteres)',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'maxlength': '20',
            'placeholder': 'N/A'
        })
    )

    dry_run = forms.BooleanField(
        label='Modo Previsualización (Dry-Run)',
        required=False,
        initial=False,
        help_text='Muestra cambios sin aplicarlos',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'dry_run_ordenes_check'
        })
    )

    def clean_archivo(self):
        archivo = self.cleaned_data.get('archivo')
        if not archivo:
            raise ValidationError('Debes seleccionar un archivo')
        nombre = archivo.name.lower()
        if not (nombre.endswith('.xlsx') or nombre.endswith('.xls')):
            raise ValidationError('El archivo debe ser Excel (.xlsx o .xls)')
        if archivo.size > 10 * 1024 * 1024:
            raise ValidationError('El archivo no debe exceder 10MB')
        return archivo

    def clean_partida_default(self):
        val = self.cleaned_data.get('partida_default', 'N/A') or 'N/A'
        return str(val)[:20]
