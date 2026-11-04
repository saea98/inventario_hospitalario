from django import forms
from django.contrib import admin, messages

from .interop_models import ApiConsumidor


class ApiConsumidorAdminForm(forms.ModelForm):
    class Meta:
        model = ApiConsumidor
        fields = (
            'nombre',
            'descripcion',
            'activo',
            'scopes',
            'institucion',
            'contacto',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields['scopes'].initial = list(ApiConsumidor.SCOPES_DEFAULT)


@admin.register(ApiConsumidor)
class ApiConsumidorAdmin(admin.ModelAdmin):
    form = ApiConsumidorAdminForm
    list_display = (
        'nombre',
        'key_prefix',
        'activo',
        'institucion',
        'ultimo_uso',
        'fecha_creacion',
    )
    list_filter = ('activo', 'institucion')
    search_fields = ('nombre', 'key_prefix', 'contacto', 'descripcion')
    readonly_fields = ('key_prefix', 'fecha_creacion', 'fecha_actualizacion', 'ultimo_uso')
    fieldsets = (
        (None, {
            'fields': ('nombre', 'descripcion', 'activo', 'contacto'),
        }),
        ('Acceso', {
            'fields': ('scopes', 'institucion', 'key_prefix'),
            'description': (
                'Al crear un consumidor se genera una API key. '
                'Cópiala del mensaje de aviso: no se vuelve a mostrar. '
                'Header HTTP: X-API-Key'
            ),
        }),
        ('Auditoría', {
            'fields': ('ultimo_uso', 'fecha_creacion', 'fecha_actualizacion'),
        }),
    )

    def save_model(self, request, obj, form, change):
        raw_key = None
        if not change or not obj.key_hash:
            raw_key = ApiConsumidor.generar_clave()
            obj.key_prefix = raw_key[:10]
            obj.key_hash = ApiConsumidor.hash_key(raw_key)
            if not obj.scopes:
                obj.scopes = list(ApiConsumidor.SCOPES_DEFAULT)
        super().save_model(request, obj, form, change)
        if raw_key:
            messages.warning(
                request,
                f'API key generada (guárdala ahora, no se vuelve a mostrar): {raw_key}',
            )

    actions = ['regenerar_api_key']

    @admin.action(description='Regenerar API key (invalida la anterior)')
    def regenerar_api_key(self, request, queryset):
        for obj in queryset:
            raw = ApiConsumidor.generar_clave()
            obj.key_prefix = raw[:10]
            obj.key_hash = ApiConsumidor.hash_key(raw)
            obj.save(update_fields=['key_prefix', 'key_hash', 'fecha_actualizacion'])
            messages.warning(request, f'{obj.nombre}: nueva API key → {raw}')
