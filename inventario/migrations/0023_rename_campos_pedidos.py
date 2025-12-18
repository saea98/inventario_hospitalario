# Generated migration to fix field names in pedidos tables

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0022_fase_2_2_1_pedidos'),
    ]

    operations = [
        # Renombrar usuario_solicita a usuario_solicitante en SolicitudPedido
        migrations.RenameField(
            model_name='solicitudpedido',
            old_name='usuario_solicita',
            new_name='usuario_solicitante',
        ),
        
        # Renombrar usuario_autoriza a usuario_validacion en SalidaExistencias
        migrations.RenameField(
            model_name='salidaexistencias',
            old_name='usuario_autoriza',
            new_name='usuario_validacion',
        ),
    ]
