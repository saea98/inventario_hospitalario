from django import forms
from .models import Proveedor

class ReporteEntradasForm(forms.Form):
    fecha_inicio = forms.DateField(required=False, widget=forms.DateInput(attrs={
        'type': 'date', 'class': 'form-control'
    }))
    fecha_fin = forms.DateField(required=False, widget=forms.DateInput(attrs={
        'type': 'date', 'class': 'form-control'
    }))
    proveedor = forms.ModelChoiceField(queryset=Proveedor.objects.all(), required=False, widget=forms.Select(attrs={
        'class': 'form-control'
    }))
    clave = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'Clave CNIS'
    }))
    lote = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'Número de lote'
    }))
