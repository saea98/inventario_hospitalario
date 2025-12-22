# 🔐 Sistema de Control de Acceso Centralizado

## Descripción General

Este sistema sincroniza el control de acceso en toda la aplicación usando **MenuItemRol** como fuente única de verdad.

**Antes:** Había dos sistemas desincronizados:
- ❌ MenuItemRol (configuración en BD)
- ❌ Template hardcodeado (código fijo)
- ❌ Decoradores (código fijo)

**Ahora:** Un sistema centralizado:
- ✅ MenuItemRol (fuente única de verdad)
- ✅ Template dinámico (lee de MenuItemRol)
- ✅ Decoradores dinámicos (validan contra MenuItemRol)

---

## 🏗️ Arquitectura

```
MenuItemRol (Base de Datos)
    ↓
    ├─→ Template Tag menu_tags.py (Renderiza menú)
    ├─→ Decorador @requiere_acceso_menuitem (Valida acceso)
    └─→ Funciones auxiliares (Verifican permisos)
```

---

## 📝 Componentes

### 1. **MenuItemRol** (Modelo)
Define qué roles pueden acceder a cada vista.

```python
class MenuItemRol(models.Model):
    menu_item = CharField()           # Identificador único
    nombre_mostrado = CharField()     # Nombre que se muestra
    url_name = CharField()            # Nombre de URL en urls.py
    roles_permitidos = ManyToManyField(Group)  # Roles que pueden acceder
    activo = BooleanField()           # Si está activo o no
```

### 2. **Template Tags** (`menu_tags.py`)
Renderiza el menú dinámicamente desde MenuItemRol.

```html
{% load menu_tags %}
{% obtener_items_menu_principales user as menu_items %}

{% for item in menu_items %}
    <a href="{% url item.url_name %}">{{ item.nombre_mostrado }}</a>
{% endfor %}
```

### 3. **Decoradores Dinámicos** (`access_control_dynamic.py`)

#### `@requiere_acceso_menuitem`
Valida acceso contra MenuItemRol automáticamente.

```python
@requiere_acceso_menuitem
def mi_vista(request):
    # Acceso validado contra MenuItemRol
    pass
```

#### `@requiere_rol_menuitem(*roles)`
Valida roles específicos y compara contra MenuItemRol.

```python
@requiere_rol_menuitem('Almacenero', 'Administrador')
def mi_vista(request):
    # Acceso validado
    pass
```

### 4. **Funciones Auxiliares** (`access_control_dynamic.py`)

```python
# Obtener roles permitidos para una URL
roles = obtener_roles_permitidos_url('lista_lotes')

# Verificar si usuario puede acceder a una URL
if usuario_puede_acceder_url(request.user, 'lista_lotes'):
    # Usuario puede acceder

# Obtener todas las URLs accesibles para un usuario
urls = obtener_urls_accesibles_usuario(request.user)
```

---

## 🚀 Cómo Usar

### Paso 1: Configurar en MenuItemRol

En Django Admin:
1. Ve a `Inventario → Menu Item Rol`
2. Crea/edita un item
3. Especifica:
   - **Nombre de URL**: `lista_lotes`
   - **Roles Permitidos**: Almacenero, Administrador
   - **Activo**: Sí

### Paso 2: Usar en la Vista

```python
from inventario.access_control_dynamic import requiere_acceso_menuitem

@requiere_acceso_menuitem
def lista_lotes(request):
    # Automáticamente valida contra MenuItemRol
    # Si el usuario no tiene acceso, lo redirige a dashboard
    return render(request, 'lotes/lista.html')
```

### Paso 3: Usar en el Template

```html
{% load menu_tags %}

<!-- Menú dinámico -->
{% obtener_items_menu_principales user as menu_items %}
{% for item in menu_items %}
    <a href="{% url item.url_name %}">{{ item.nombre_mostrado }}</a>
{% endfor %}

<!-- Verificar acceso a una URL específica -->
{% if user|puede_acceder_url:"lista_lotes" %}
    <a href="{% url 'lista_lotes' %}">Lotes</a>
{% endif %}
```

---

## 🔍 Validación y Debugging

### Comando: Validar Control de Acceso

```bash
# Ver desajustes
python manage.py validar_control_acceso --verbose

# Ver solo resumen
python manage.py validar_control_acceso
```

**Salida esperada:**
```
================================================================================
VALIDACIÓN DE CONTROL DE ACCESO
================================================================================

✅ lista_lotes: MenuItemRol={Almacenero, Administrador}
✅ lista_productos: MenuItemRol={Administrador}
...

================================================================================
RESUMEN
================================================================================
Total de URLs: 45
Desajustes: 0
Vistas sin MenuItemRol: 3
================================================================================
```

### Console del Navegador

```javascript
// Ver roles del usuario
debugLogger.showUserRolesTable()

// Ver items del menú
debugLogger.showMenuItemsTable()

// Ver historial de acceso
debugLogger.showLogs()
```

---

## ⚠️ Casos Comunes

### Caso 1: Usuario no ve un menú que debería ver

**Diagnóstico:**
```bash
# 1. Verificar MenuItemRol
python manage.py validar_control_acceso --verbose

# 2. En consola del navegador
debugLogger.showUserRolesTable()
debugLogger.showMenuItemsTable()

# 3. Verificar que el usuario tenga el rol
# En Django Admin → Usuarios → Seleccionar usuario → Grupos
```

### Caso 2: Usuario ve un menú que NO debería ver

**Diagnóstico:**
```bash
# 1. Verificar MenuItemRol
python manage.py validar_control_acceso --verbose

# 2. Verificar que el rol está correctamente asignado en MenuItemRol
# En Django Admin → Menu Item Rol → Seleccionar item → Roles Permitidos
```

### Caso 3: Desajuste entre decorador y MenuItemRol

**Diagnóstico:**
```bash
# El comando mostrará algo como:
# ❌ DESAJUSTES ENCONTRADOS:
#   • lista_lotes (Existencias)
#     Decorador: {Almacenero, Administrador}
#     MenuItemRol: {Administrador}

# Solución: Actualizar MenuItemRol en Django Admin
```

---

## 📋 Migración desde Sistema Anterior

Si tienes vistas con decoradores hardcodeados:

**Antes:**
```python
@login_required
@requiere_rol('Almacenero', 'Administrador')
def mi_vista(request):
    pass
```

**Después:**
```python
from inventario.access_control_dynamic import requiere_acceso_menuitem

@requiere_acceso_menuitem
def mi_vista(request):
    pass
```

**Pasos:**
1. Crear/actualizar item en MenuItemRol
2. Cambiar decorador a `@requiere_acceso_menuitem`
3. Ejecutar `python manage.py validar_control_acceso` para verificar

---

## 🛡️ Seguridad

### Validaciones Múltiples

1. **Decorador**: Valida en tiempo de ejecución
2. **Template**: No renderiza items no permitidos
3. **MenuItemRol**: Fuente única de verdad

### Flujo de Acceso

```
Usuario intenta acceder a /lista_lotes/
    ↓
Decorador @requiere_acceso_menuitem
    ↓
¿Usuario autenticado? → No → Redirigir a login
    ↓ Sí
¿Es superusuario? → Sí → Permitir acceso
    ↓ No
Buscar en MenuItemRol (url_name='lista_lotes')
    ↓
¿Usuario tiene algún rol permitido? → No → Redirigir a dashboard
    ↓ Sí
Permitir acceso
```

---

## 📊 Monitoreo

### Logs

Los decoradores registran:
- ✅ Acceso permitido
- ❌ Acceso denegado
- ⚠️ Desajustes entre decorador y MenuItemRol

```python
# En logs de Django
logger.info(f"Acceso permitido a {request.user.username} en {url_name}")
logger.warning(f"Acceso denegado a {request.user.username} en {url_name}")
logger.warning(f"DESAJUSTE en {url_name}: ...")
```

### Console del Navegador

```javascript
// Ver todos los logs de acceso
debugLogger.showLogs()

// Exportar para análisis
debugLogger.exportLogs()
```

---

## 🔄 Sincronización Automática

Para mantener sincronizado:

1. **Cambios en MenuItemRol** → Automáticamente afecta menú y decoradores
2. **Cambios en decoradores** → Ejecutar `validar_control_acceso` para detectar desajustes
3. **Cambios en template** → Usar template tags dinámicos

---

## 📚 Referencia Rápida

| Tarea | Solución |
|-------|----------|
| Agregar acceso a una vista | Crear/editar MenuItemRol |
| Quitar acceso a una vista | Desactivar MenuItemRol o remover rol |
| Verificar desajustes | `python manage.py validar_control_acceso` |
| Debuggear acceso | `debugLogger.showLogs()` en consola |
| Obtener URLs accesibles | `obtener_urls_accesibles_usuario(user)` |
| Verificar acceso a URL | `usuario_puede_acceder_url(user, 'url_name')` |

---

## ✅ Checklist de Implementación

- [ ] Crear MenuItemRol para todas las vistas
- [ ] Cambiar decoradores a `@requiere_acceso_menuitem`
- [ ] Reemplazar menú hardcodeado con template dinámico
- [ ] Ejecutar `validar_control_acceso` y corregir desajustes
- [ ] Probar con diferentes roles
- [ ] Verificar logs en consola del navegador
- [ ] Documentar cambios

---

## 🆘 Troubleshooting

### El menú no se actualiza después de cambiar MenuItemRol

**Solución:**
1. Limpiar caché: `python manage.py clear_cache`
2. Recargar página en navegador: `Ctrl+Shift+R`
3. Verificar que MenuItemRol esté activo

### Usuario ve menú pero no puede acceder

**Solución:**
1. Verificar que el decorador esté aplicado
2. Ejecutar `validar_control_acceso` para detectar desajustes
3. Verificar roles en Django Admin

### Desajustes entre decorador y MenuItemRol

**Solución:**
1. Ejecutar `validar_control_acceso --verbose`
2. Actualizar MenuItemRol o decorador según sea necesario
3. Ejecutar nuevamente para verificar

---

## 📞 Soporte

Para problemas o preguntas:

1. Ejecutar `python manage.py validar_control_acceso --verbose`
2. Ver logs en consola: `debugLogger.showLogs()`
3. Revisar Django Admin → Menu Item Rol
4. Contactar al equipo de desarrollo
