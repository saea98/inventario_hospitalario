from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('inventario', '0028_create_roles'),
    ]

    operations = [
        migrations.CreateModel(
            name='MenuItemRol',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('menu_item', models.CharField(
                    choices=[
                        ('dashboard', 'Dashboard'),
                        ('instituciones', 'Instituciones'),
                        ('productos', 'Productos'),
                        ('proveedores', 'Proveedores'),
                        ('alcaldias', 'Alcaldías'),
                        ('almacenes', 'Almacenes'),
                        ('existencias', 'Existencias'),
                        ('entrada_almacen', 'Entrada al Almacén'),
                        ('salidas_almacen', 'Salidas del Almacén'),
                        ('citas', 'Citas de Proveedores'),
                        ('traslados', 'Traslados'),
                        ('conteo_fisico', 'Conteo Físico'),
                        ('gestion_pedidos', 'Gestión de Pedidos'),
                        ('propuestas_surtimiento', 'Propuestas de Surtimiento'),
                        ('llegada_proveedores', 'Llegada de Proveedores'),
                        ('devoluciones', 'Devoluciones de Proveedores'),
                        ('reportes_devoluciones', 'Reportes de Devoluciones'),
                        ('reportes_salidas', 'Reportes de Salidas'),
                        ('inventario', 'Inventario'),
                        ('alertas', 'Alertas'),
                        ('solicitudes', 'Solicitudes'),
                        ('cargas_masivas', 'Cargas Masivas'),
                        ('picking', 'Picking y Operaciones'),
                        ('administracion', 'Administración'),
                    ],
                    max_length=50,
                    unique=True,
                    verbose_name='Opción de Menú'
                )),
                ('nombre_mostrado', models.CharField(max_length=100, verbose_name='Nombre Mostrado')),
                ('icono', models.CharField(default='fas fa-circle', max_length=50, verbose_name='Icono Font Awesome')),
                ('url_name', models.CharField(max_length=100, verbose_name='Nombre de URL')),
                ('orden', models.IntegerField(default=0, verbose_name='Orden')),
                ('activo', models.BooleanField(default=True, verbose_name='Activo')),
                ('es_submenu', models.BooleanField(default=False, verbose_name='Es Submenú')),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('fecha_actualizacion', models.DateTimeField(auto_now=True)),
                ('menu_padre', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='submenus', to='inventario.menuitemrol', verbose_name='Menú Padre')),
                ('roles_permitidos', models.ManyToManyField(to='auth.group', verbose_name='Roles Permitidos')),
            ],
            options={
                'verbose_name': 'Configuración de Menú por Rol',
                'verbose_name_plural': 'Configuraciones de Menú por Rol',
                'ordering': ['orden', 'nombre_mostrado'],
            },
        ),
    ]
