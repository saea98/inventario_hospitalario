from django import forms

class RawSQLForm(forms.Form):
    sql_query = forms.CharField(
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 10,
            "placeholder": "-- Escribe tu consulta SQL aquí...\nSELECT * FROM inventario_lote WHERE cantidad_disponible > 100;"
        }),
        label="Consulta SQL",
        help_text="Ejecuta consultas SQL directamente en la base de datos. Solo para administradores."
    )
