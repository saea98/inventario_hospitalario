# 📋 Guía de Gestión de Roles del Sistema

## Roles Disponibles

El sistema cuenta con los siguientes **10 roles** basados en el Manual de Procedimientos del Almacén:

| Rol | Descripción |
|-----|-------------|
| **Revisión** | Responsable de revisar y autorizar citas y pedidos |
| **Almacenero** | Responsable de recepción, almacenamiento y picking |
| **Control Calidad** | Responsable de inspeccionar productos |
| **Facturación** | Responsable de registrar facturas |
| **Supervisión** | Responsable de supervisar y validar operaciones |
| **Logística** | Responsable de asignación de logística y traslados |
| **Recepción** | Responsable de recepción en destino de traslados |
| **Conteo** | Responsable de realizar conteos físicos |
| **Gestor de Inventario** | Responsable de gestión general del inventario |
| **Administrador** | Administrador del sistema |

---

## Crear Roles

### Opción 1: Comando de Django (Recomendado)

```bash
docker-compose exec web python manage.py crear_roles
```

Este comando:
- ✅ Crea automáticamente todos los 10 roles
- ✅ Verifica si ya existen (no crea duplicados)
- ✅ Muestra un resumen de los roles creados

### Opción 2: Panel de Administración

1. Accede a: `http://tu-servidor/admin/auth/group/`
2. Haz clic en "Agregar grupo"
3. Ingresa el nombre del rol
4. Asigna permisos si es necesario
5. Haz clic en "Guardar"

---

## Asignar Roles a Usuarios

### Desde Django Admin

1. Accede a: `http://tu-servidor/admin/auth/user/`
2. Selecciona el usuario
3. En la sección "Grupos", selecciona los roles que deseas asignar
4. Haz clic en "Guardar"

### Desde la Línea de Comandos

```bash
docker-compose exec web python manage.py shell
```

```python
from django.contrib.auth.models import User, Group

# Obtener el usuario
usuario = User.objects.get(username='nombre_usuario')

# Obtener el grupo
grupo = Group.objects.get(name='Almacenero')

# Asignar el grupo al usuario
usuario.groups.add(grupo)

# Confirmar
print(f"Grupos del usuario: {usuario.groups.all()}")
```

---

## Verificar Roles Asignados

### Desde Django Admin

1. Accede a: `http://tu-servidor/admin/auth/user/`
2. Selecciona el usuario
3. Verifica la sección "Grupos"

### Desde la Línea de Comandos

```bash
docker-compose exec web python manage.py shell
```

```python
from django.contrib.auth.models import User

# Obtener el usuario
usuario = User.objects.get(username='nombre_usuario')

# Ver sus grupos
print(f"Grupos del usuario {usuario.username}:")
for grupo in usuario.groups.all():
    print(f"  - {grupo.name}")
```

---

## Listar Todos los Roles

### Desde la Línea de Comandos

```bash
docker-compose exec web python manage.py shell
```

```python
from django.contrib.auth.models import Group

# Listar todos los grupos
print("Roles disponibles en el sistema:")
for grupo in Group.objects.all().order_by('name'):
    print(f"  • {grupo.name}")
```

---

## Eliminar un Rol

⚠️ **ADVERTENCIA**: Eliminar un rol desasignará automáticamente ese rol de todos los usuarios.

### Desde Django Admin

1. Accede a: `http://tu-servidor/admin/auth/group/`
2. Selecciona el rol a eliminar
3. Haz clic en "Eliminar"
4. Confirma la acción

### Desde la Línea de Comandos

```bash
docker-compose exec web python manage.py shell
```

```python
from django.contrib.auth.models import Group

# Obtener el grupo
grupo = Group.objects.get(name='Nombre del Rol')

# Eliminar
grupo.delete()
print("Rol eliminado")
```

---

## Verificar Permisos de un Usuario

```bash
docker-compose exec web python manage.py shell
```

```python
from django.contrib.auth.models import User

# Obtener el usuario
usuario = User.objects.get(username='nombre_usuario')

# Ver sus permisos
print(f"Permisos del usuario {usuario.username}:")
for permiso in usuario.get_all_permissions():
    print(f"  - {permiso}")

# Ver sus grupos
print(f"\nGrupos del usuario:")
for grupo in usuario.groups.all():
    print(f"  - {grupo.name}")
```

---

## Notas Importantes

- Los roles se almacenan en la tabla `auth_group` de la base de datos
- Los usuarios pueden tener múltiples roles asignados
- Los roles se utilizan en los decoradores `@requiere_rol()` para controlar el acceso a vistas
- Los cambios de roles se aplican inmediatamente sin necesidad de reiniciar el servidor

---

## Troubleshooting

### Los roles no aparecen en Django Admin

1. Verifica que la migración se ejecutó:
   ```bash
   docker-compose exec web python manage.py showmigrations inventario | grep 0028
   ```

2. Si no aparece, ejecuta las migraciones:
   ```bash
   docker-compose exec web python manage.py migrate
   ```

3. Luego ejecuta el comando para crear roles:
   ```bash
   docker-compose exec web python manage.py crear_roles
   ```

### Un usuario no puede acceder a una vista

1. Verifica que el usuario tiene el rol correcto asignado
2. Verifica que el rol está en el decorador `@requiere_rol()` de la vista
3. Limpia el caché del navegador (Ctrl+Shift+Del)
4. Cierra sesión y vuelve a iniciar sesión

---

**Última actualización**: Diciembre 2025
