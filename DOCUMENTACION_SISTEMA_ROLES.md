# 📚 Documentación Completa del Sistema de Gestión de Roles

## Índice

1. [Introducción](#introducción)
2. [Arquitectura del Sistema](#arquitectura-del-sistema)
3. [Componentes Principales](#componentes-principales)
4. [Configuración Inicial](#configuración-inicial)
5. [Gestión de Usuarios y Roles](#gestión-de-usuarios-y-roles)
6. [Control de Acceso](#control-de-acceso)
7. [Menú Dinámico](#menú-dinámico)
8. [Dashboard de Administración](#dashboard-de-administración)
9. [Ejemplos Prácticos](#ejemplos-prácticos)
10. [Troubleshooting](#troubleshooting)

---

## Introducción

El sistema de gestión de roles implementa un control de acceso basado en roles (RBAC) que permite:

- ✅ Asignar múltiples roles a cada usuario
- ✅ Controlar acceso a vistas según roles
- ✅ Mostrar/ocultar opciones de menú dinámicamente
- ✅ Configurar permisos granulares por rol
- ✅ Administrar todo desde una interfaz visual

El sistema está basado en el **Manual de Procedimientos del Almacén** y define 10 roles principales.

---

## Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                    USUARIO AUTENTICADO                      │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
    ┌─────────┐   ┌─────────┐   ┌──────────────┐
    │  ROLES  │   │PERMISOS │   │OPCIONES MENÚ │
    │ (Groups)│   │(Django) │   │(MenuItemRol) │
    └────┬────┘   └────┬────┘   └──────┬───────┘
         │             │                │
         └─────────────┼────────────────┘
                       │
         ┌─────────────┼─────────────┐
         │             │             │
         ▼             ▼             ▼
    ┌─────────┐  ┌──────────┐  ┌──────────┐
    │ VISTAS  │  │TEMPLATES │  │MIDDLEWARE│
    │(Control)│  │(Mostrar) │  │(Verificar)
    └─────────┘  └──────────┘  └──────────┘
```

---

## Componentes Principales

### 1. **Modelos**

#### `User` (Modelo Personalizado)
```python
class User(AbstractUser):
    clue = models.CharField(...)
    almacen = models.ForeignKey(Almacen, ...)
```

#### `MenuItemRol`
Define qué opciones de menú puede ver cada rol.

```python
class MenuItemRol(models.Model):
    menu_item = CharField(choices=MENU_CHOICES)
    nombre_mostrado = CharField()
    icono = CharField()
    url_name = CharField()
    roles_permitidos = ManyToManyField(Group)
    activo = BooleanField()
    orden = IntegerField()
```

### 2. **Decoradores** (`access_control.py`)

- `@requiere_rol()` - Requiere uno de los roles
- `@requiere_roles_todos()` - Requiere todos los roles
- `@requiere_permiso()` - Requiere permisos específicos
- `@requiere_rol_o_permiso()` - Requiere rol O permiso

### 3. **Middleware** (`middleware.py`)

- `ControlAccesoRolesMiddleware` - Verifica acceso global
- `AgregarContextoAccesoMiddleware` - Agrega contexto al request

### 4. **Vistas de Administración** (`admin_roles_views.py`)

- Dashboard principal
- Gestión de usuarios
- Gestión de roles
- Configuración de menú
- Reportes y estadísticas

---

## Configuración Inicial

### Paso 1: Crear Roles

```bash
docker-compose exec web python manage.py crear_roles
```

Crea los 10 roles del sistema:
1. Administrador
2. Almacenero
3. Control Calidad
4. Facturación
5. Supervisión
6. Logística
7. Recepción
8. Conteo
9. Gestor de Inventario
10. Revisión

### Paso 2: Cargar Configuración de Menú

```bash
docker-compose exec web python manage.py cargar_menu_roles
```

Carga las opciones de menú y asigna roles permitidos.

### Paso 3: Configurar Permisos

```bash
docker-compose exec web python manage.py configurar_permisos_roles
```

Asigna permisos específicos a cada rol.

### Paso 4: Crear Usuarios de Ejemplo (Opcional)

```bash
docker-compose exec web python manage.py cargar_usuarios_ejemplo
```

Crea 10 usuarios de ejemplo con roles predefinidos.

---

## Gestión de Usuarios y Roles

### Asignar Roles a un Usuario

**Opción 1: Comando de línea**

```bash
docker-compose exec web python manage.py gestionar_roles asignar \
  --usuario=juan \
  --rol=Almacenero
```

**Opción 2: Dashboard Web**

1. Accede a: `http://tu-servidor/admin-roles/usuarios/`
2. Selecciona el usuario
3. Marca los roles deseados
4. Guarda los cambios

**Opción 3: Django Admin**

1. Accede a: `http://tu-servidor/admin/auth/user/`
2. Selecciona el usuario
3. En "Grupos", selecciona los roles
4. Guarda

### Verificar Roles de un Usuario

```bash
docker-compose exec web python manage.py gestionar_roles ver-usuario --usuario=juan
```

Muestra:
- Roles asignados
- Permisos asociados
- Opciones de menú disponibles

---

## Control de Acceso

### En Vistas

```python
from inventario.access_control import requiere_rol

@requiere_rol('Almacenero', 'Supervisión')
def mi_vista(request):
    return render(request, 'template.html')
```

### En Templates

```html
{% if 'Almacenero' in user.groups.values_list.name %}
    <a href="{% url 'picking:dashboard' %}">Picking</a>
{% endif %}
```

### En Python

```python
from inventario.access_control import usuario_tiene_rol

if usuario_tiene_rol(request.user, 'Almacenero'):
    # hacer algo
```

---

## Menú Dinámico

### Cómo Funciona

1. El usuario accede a la aplicación
2. El template `base.html` carga el menú dinámico
3. El template tag `menu_dinamico` obtiene las opciones permitidas
4. Solo se muestran las opciones según los roles del usuario

### Configurar el Menú

1. Accede a: `http://tu-servidor/admin-roles/menu/`
2. Edita cada opción
3. Selecciona los roles permitidos
4. Activa/desactiva según sea necesario

---

## Dashboard de Administración

Accede a: `http://tu-servidor/admin-roles/`

### Opciones Disponibles

| Opción | Descripción |
|--------|-------------|
| **Usuarios** | Gestionar usuarios y asignar roles |
| **Roles** | Ver roles y usuarios asignados |
| **Menú** | Configurar opciones de menú por rol |
| **Reportes** | Matriz de acceso usuario-opción |
| **Estadísticas** | Gráficos y análisis de roles |

---

## Ejemplos Prácticos

### Ejemplo 1: Crear un Nuevo Usuario con Rol

```bash
# Crear usuario
docker-compose exec web python manage.py crear_usuario_rol

# Seguir las instrucciones interactivas
```

### Ejemplo 2: Restringir Acceso a una Vista

```python
from inventario.access_control import requiere_rol
from django.shortcuts import render

@requiere_rol('Supervisión', 'Administrador')
def reporte_general(request):
    # Solo Supervisión y Administrador pueden acceder
    datos = obtener_datos_reporte()
    return render(request, 'reportes/general.html', {'datos': datos})
```

### Ejemplo 3: Mostrar/Ocultar Elemento en Template

```html
{% if user.is_superuser or 'Administrador' in user.groups.values_list.name %}
    <div class="admin-panel">
        <a href="{% url 'admin_roles:dashboard' %}">
            <i class="fas fa-user-shield"></i>
            Administración de Roles
        </a>
    </div>
{% endif %}
```

### Ejemplo 4: Verificar Múltiples Roles

```python
from inventario.access_control import usuario_tiene_rol, usuario_tiene_todos_roles

def mi_vista(request):
    # Verificar si tiene UNO de los roles
    if usuario_tiene_rol(request.user, 'Almacenero', 'Supervisión'):
        # hacer algo
        pass
    
    # Verificar si tiene TODOS los roles
    if usuario_tiene_todos_roles(request.user, 'Almacenero', 'Supervisión'):
        # hacer algo más específico
        pass
```

---

## Roles del Sistema

### 1. **Administrador**
- Acceso total al sistema
- Gestión de usuarios y roles
- Configuración de menú
- Ver todos los reportes

### 2. **Almacenero**
- Entrada al almacén
- Picking y operaciones
- Gestión de existencias
- Devoluciones

### 3. **Supervisión**
- Ver todas las operaciones
- Autorizar cambios de estado
- Acceso a reportes
- Supervisar traslados

### 4. **Control Calidad**
- Inspeccionar productos
- Entrada al almacén
- Cambiar estados de lotes

### 5. **Facturación**
- Ver propuestas y solicitudes
- Gestionar facturas
- Acceso a reportes

### 6. **Revisión**
- Revisar citas
- Autorizar pedidos
- Gestión de solicitudes

### 7. **Logística**
- Gestionar traslados
- Asignar logística
- Ver propuestas

### 8. **Recepción**
- Recepción en destino
- Cambiar estado de lotes
- Confirmar traslados

### 9. **Conteo**
- Realizar conteos físicos
- Actualizar lotes
- Generar reportes de conteo

### 10. **Gestor de Inventario**
- Gestión general del inventario
- Movimientos
- Reportes de inventario

---

## Troubleshooting

### El usuario no ve las opciones de menú

1. Verifica que el usuario tiene roles asignados:
   ```bash
   docker-compose exec web python manage.py gestionar_roles ver-usuario --usuario=nombre
   ```

2. Verifica que el rol está asignado a la opción de menú:
   ```bash
   # Accede a: http://tu-servidor/admin-roles/menu/
   ```

3. Limpia el caché del navegador (Ctrl+Shift+Del)

### Error 403 Forbidden

1. Verifica que el usuario tiene el rol requerido
2. Verifica que el decorador `@requiere_rol()` está correcto
3. Cierra sesión y vuelve a iniciar sesión

### La migración falla

1. Verifica que todas las migraciones anteriores se ejecutaron:
   ```bash
   docker-compose exec web python manage.py migrate --list
   ```

2. Ejecuta las migraciones pendientes:
   ```bash
   docker-compose exec web python manage.py migrate
   ```

### Los permisos no se aplican

1. Ejecuta el comando de configuración de permisos:
   ```bash
   docker-compose exec web python manage.py configurar_permisos_roles
   ```

2. Verifica que los permisos están asignados:
   ```bash
   # Accede a: http://tu-servidor/admin/auth/group/
   ```

---

## Mejores Prácticas

1. **Siempre usar decoradores** en vistas que requieren acceso restringido
2. **Mantener consistencia** en nombres de roles
3. **Documentar** qué roles pueden acceder a cada vista
4. **Probar con diferentes usuarios** para verificar el acceso
5. **Usar template tags** para mostrar/ocultar elementos dinámicamente
6. **Configurar el menú** desde el dashboard, no en código
7. **Revisar reportes de acceso** regularmente

---

## Comandos Disponibles

| Comando | Descripción |
|---------|-------------|
| `crear_roles` | Crear los 10 roles del sistema |
| `cargar_menu_roles` | Cargar configuración de menú |
| `configurar_permisos_roles` | Asignar permisos a roles |
| `gestionar_roles` | Gestionar roles de usuarios |
| `crear_usuario_rol` | Crear usuario con rol |
| `cargar_usuarios_ejemplo` | Crear usuarios de ejemplo |

---

## URLs Disponibles

| URL | Descripción |
|-----|-------------|
| `/admin-roles/` | Dashboard principal |
| `/admin-roles/usuarios/` | Gestión de usuarios |
| `/admin-roles/usuarios/<id>/editar/` | Editar roles de usuario |
| `/admin-roles/roles/` | Listar roles |
| `/admin-roles/roles/<id>/` | Detalle de rol |
| `/admin-roles/menu/` | Configurar opciones de menú |
| `/admin-roles/menu/<id>/editar/` | Editar opción de menú |
| `/admin-roles/reporte-acceso/` | Matriz de acceso |
| `/admin-roles/estadisticas/` | Estadísticas y gráficos |

---

## Soporte y Documentación Adicional

- **GUIA_ROLES.md** - Guía básica de creación de roles
- **GUIA_ASIGNAR_ROLES.md** - Guía de asignación de roles
- **GUIA_CONTROL_ACCESO.md** - Guía de control de acceso en vistas
- **Manual de Procedimientos del Almacén** - Documento de referencia

---

**Última actualización**: Diciembre 2025

**Versión**: 1.0

**Autor**: Sistema de Gestión de Roles
