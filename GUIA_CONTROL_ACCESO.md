# 🔐 Guía de Control de Acceso Basado en Roles

## Introducción

El sistema implementa un control de acceso completo basado en roles que permite:

- ✅ Restringir acceso a vistas según roles del usuario
- ✅ Mostrar/ocultar opciones de menú dinámicamente
- ✅ Verificar permisos en templates
- ✅ Control granular de acceso a funcionalidades

---

## Decoradores para Vistas

### 1. `@requiere_rol()` - Requiere uno de los roles

```python
from inventario.access_control import requiere_rol

@requiere_rol('Almacenero', 'Supervisión')
def mi_vista(request):
    # Solo usuarios con rol Almacenero O Supervisión pueden acceder
    return render(request, 'template.html')
```

### 2. `@requiere_roles_todos()` - Requiere TODOS los roles

```python
from inventario.access_control import requiere_roles_todos

@requiere_roles_todos('Almacenero', 'Supervisión')
def mi_vista(request):
    # Usuario debe tener AMBOS roles
    return render(request, 'template.html')
```

### 3. `@requiere_permiso()` - Requiere permisos específicos

```python
from inventario.access_control import requiere_permiso

@requiere_permiso('inventario.add_lote', 'inventario.change_lote')
def mi_vista(request):
    # Usuario debe tener ambos permisos
    return render(request, 'template.html')
```

### 4. `@requiere_rol_o_permiso()` - Requiere rol O permiso

```python
from inventario.access_control import requiere_rol_o_permiso

@requiere_rol_o_permiso(
    roles=['Almacenero', 'Administrador'],
    permisos=['inventario.add_lote']
)
def mi_vista(request):
    # Usuario puede tener el rol O el permiso
    return render(request, 'template.html')
```

---

## Funciones Auxiliares

### Verificar roles en vistas

```python
from inventario.access_control import usuario_tiene_rol, usuario_tiene_todos_roles

def mi_vista(request):
    # Verificar si tiene uno de los roles
    if usuario_tiene_rol(request.user, 'Almacenero', 'Supervisión'):
        # hacer algo
        pass
    
    # Verificar si tiene todos los roles
    if usuario_tiene_todos_roles(request.user, 'Almacenero', 'Supervisión'):
        # hacer algo
        pass
```

### Obtener información de acceso

```python
from inventario.access_control import obtener_roles_usuario, obtener_permisos_usuario

def mi_vista(request):
    roles = obtener_roles_usuario(request.user)
    # roles = ['Almacenero', 'Supervisión']
    
    permisos = obtener_permisos_usuario(request.user)
    # permisos = ['inventario.add_lote', 'inventario.change_lote', ...]
```

---

## Mixins para Vistas Basadas en Clases

### RequiereRolMixin

```python
from django.views import View
from inventario.access_control import RequiereRolMixin

class MiVista(RequiereRolMixin, View):
    roles_requeridos = ['Almacenero', 'Administrador']
    
    def get(self, request):
        return render(request, 'template.html')
```

### RequierePermisoMixin

```python
from django.views import View
from inventario.access_control import RequierePermisoMixin

class MiVista(RequierePermisoMixin, View):
    permisos_requeridos = ['inventario.add_lote']
    
    def get(self, request):
        return render(request, 'template.html')
```

---

## Control en Templates

### Verificar rol en template

```html
{% if user.groups.all|length > 0 %}
    <p>Tienes los siguientes roles:</p>
    <ul>
    {% for grupo in user.groups.all %}
        <li>{{ grupo.name }}</li>
    {% endfor %}
    </ul>
{% endif %}
```

### Usar contexto de acceso

```html
{% load menu_tags %}

{% if user.is_superuser %}
    <a href="{% url 'admin:index' %}">Panel de Administración</a>
{% endif %}

{% if user.groups.all|length > 0 %}
    <p>Roles: {{ user.groups.all|join:", " }}</p>
{% endif %}
```

### Mostrar/ocultar elementos según rol

```html
{% if 'Almacenero' in user.groups.values_list.name %}
    <a href="{% url 'picking:dashboard' %}">Picking</a>
{% endif %}

{% if 'Supervisión' in user.groups.values_list.name %}
    <a href="{% url 'logistica:lista_propuestas' %}">Propuestas</a>
{% endif %}
```

---

## Configuración en Django Admin

### Gestionar Roles

1. Accede a: `http://tu-servidor/admin/auth/group/`
2. Crea o edita grupos (roles)
3. Asigna permisos a los grupos

### Gestionar Acceso al Menú

1. Accede a: `http://tu-servidor/admin/inventario/menuitemrol/`
2. Edita cada opción de menú
3. Selecciona los roles que pueden verla
4. Guarda los cambios

### Asignar Roles a Usuarios

1. Accede a: `http://tu-servidor/admin/auth/user/`
2. Selecciona el usuario
3. En "Grupos", selecciona los roles
4. Guarda los cambios

---

## Ejemplos Prácticos

### Ejemplo 1: Vista de Entrada al Almacén

```python
from django.shortcuts import render
from inventario.access_control import requiere_rol

@requiere_rol('Almacenero', 'Supervisión')
def entrada_almacen(request):
    # Solo Almacenero y Supervisión pueden acceder
    return render(request, 'entrada_almacen.html')
```

### Ejemplo 2: Vista de Reportes

```python
from django.shortcuts import render
from inventario.access_control import requiere_rol

@requiere_rol('Supervisión', 'Administrador')
def reporte_general(request):
    # Solo Supervisión y Administrador pueden ver reportes
    return render(request, 'reportes/general.html')
```

### Ejemplo 3: Vista de Administración

```python
from django.shortcuts import render
from inventario.access_control import requiere_rol

@requiere_rol('Administrador')
def panel_admin(request):
    # Solo Administrador puede acceder
    return render(request, 'admin/panel.html')
```

### Ejemplo 4: Vista con Múltiples Condiciones

```python
from django.shortcuts import render
from inventario.access_control import requiere_rol_o_permiso

@requiere_rol_o_permiso(
    roles=['Supervisión', 'Administrador'],
    permisos=['inventario.change_propuestapedido']
)
def editar_propuesta(request, propuesta_id):
    # Usuario puede tener el rol O el permiso
    return render(request, 'propuesta/editar.html')
```

---

## Flujo de Control de Acceso

```
Usuario accede a una URL
    ↓
¿Usuario autenticado?
    ├─ No → Redirigir a login
    └─ Sí → Continuar
    ↓
¿URL tiene decorador @requiere_rol?
    ├─ No → Permitir acceso
    └─ Sí → Verificar roles
    ↓
¿Usuario tiene rol requerido?
    ├─ No → Mostrar mensaje de error y redirigir a dashboard
    └─ Sí → Permitir acceso a la vista
```

---

## Mensajes de Error

Cuando un usuario intenta acceder a una vista sin permiso, verá un mensaje como:

> "No tienes permiso para acceder a esta sección. Se requiere uno de los siguientes roles: Almacenero, Supervisión"

---

## Troubleshooting

### El decorador no funciona

1. Verifica que el usuario tiene el rol asignado:
   ```bash
   docker-compose exec web python manage.py gestionar_roles ver-usuario --usuario=nombre_usuario
   ```

2. Verifica que el nombre del rol en el decorador coincide exactamente con el nombre en la base de datos

3. Cierra sesión y vuelve a iniciar sesión

### El menú no se actualiza

1. Verifica que MenuItemRol está configurado correctamente:
   ```bash
   docker-compose exec web python manage.py cargar_menu_roles
   ```

2. Limpia el caché del navegador (Ctrl+Shift+Del)

3. Recarga la página

### Error 403 Forbidden

1. Verifica que el usuario tiene el rol requerido
2. Verifica que la URL está configurada en MenuItemRol
3. Verifica que el rol está asignado a esa opción de menú

---

## Mejores Prácticas

1. **Siempre usar decoradores** en vistas que requieren acceso restringido
2. **Configurar el menú** en Django Admin para que sea consistente
3. **Usar nombres de rol consistentes** (ej: 'Almacenero', no 'almacenero')
4. **Documentar qué roles pueden acceder** a cada vista
5. **Probar con diferentes usuarios** para verificar el acceso

---

**Última actualización**: Diciembre 2025
