# Generated migration for CitaProveedor cancelation fields

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('inventario', '0053_logerrorpedido'),
    ]

    operations = [
        migrations.AddField(
            model_name='citaproveedor',
            name='fecha_cancelacion',
            field=models.DateTimeField(blank=True, help_text='Fecha y hora cuando se canceló la cita', null=True, verbose_name='Fecha de Cancelación'),
        ),
        migrations.AddField(
            model_name='citaproveedor',
            name='usuario_cancelacion',
            field=models.ForeignKey(blank=True, help_text='Usuario que canceló la cita', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='citas_canceladas', to=settings.AUTH_USER_MODEL, verbose_name='Usuario que Cancela'),
        ),
        migrations.AddField(
            model_name='citaproveedor',
            name='razon_cancelacion',
            field=models.TextField(blank=True, help_text='Motivo por el cual se canceló la cita', null=True, verbose_name='Razón de Cancelación'),
        ),
    ]
