# Generated migration for LogPropuesta model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('inventario', '0043_cargainventario_productos_no_procesados'),
    ]

    operations = [
        migrations.CreateModel(
            name='LogPropuesta',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('accion', models.CharField(max_length=255)),
                ('detalles', models.TextField(blank=True, null=True)),
                ('propuesta', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='logs', to='inventario.propuestapedido')),
                ('usuario', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-timestamp'],
            },
        ),
    ]
