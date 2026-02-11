# Generated manually for picking: evitar doble recogida por otro usuario

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('inventario', '0106_alter_proveedor_rfc_max_length'),
    ]

    operations = [
        migrations.AddField(
            model_name='loteasignado',
            name='usuario_surtido',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='lotes_asignados_surtidos',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Usuario que recogió',
            ),
        ),
    ]
