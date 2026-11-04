from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0111_itemtransferencia_precios'),
    ]

    operations = [
        migrations.CreateModel(
            name='ApiConsumidor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=120, verbose_name='Nombre del equipo / sistema')),
                ('descripcion', models.TextField(blank=True, default='')),
                ('key_prefix', models.CharField(db_index=True, editable=False, max_length=12)),
                ('key_hash', models.CharField(editable=False, max_length=64, unique=True)),
                ('activo', models.BooleanField(default=True)),
                ('scopes', models.JSONField(blank=True, default=list, help_text='Lista de scopes, p.ej. ["existencias:read","productos:read","lotes:read"]')),
                ('contacto', models.CharField(blank=True, default='', max_length=200)),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('fecha_actualizacion', models.DateTimeField(auto_now=True)),
                ('ultimo_uso', models.DateTimeField(blank=True, null=True)),
                ('institucion', models.ForeignKey(blank=True, help_text='Si se define, las consultas se restringen a esa institución.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='api_consumidores', to='inventario.institucion')),
            ],
            options={
                'verbose_name': 'API consumidor (interop)',
                'verbose_name_plural': 'API consumidores (interop)',
                'ordering': ['nombre'],
            },
        ),
    ]
