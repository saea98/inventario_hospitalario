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
