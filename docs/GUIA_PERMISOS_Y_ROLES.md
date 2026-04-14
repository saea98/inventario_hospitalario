# Guía de permisos y roles para administradores

Esta guía explica cómo el sistema controla el acceso y cómo un **administrador de la aplicación** puede asignar roles, afinar qué ve cada rol en el menú y cuándo hace falta usar la consola o Django Admin.

---

## ¿Se puede gestionar desde la interfaz web?

**Sí.** Quien tenga el rol **Administrador** ve en el menú **Administración de roles** (URL base **`/admin-roles/`** en el mismo sitio donde usan el inventario). Desde ahí puede:

| Acción | Pantalla |
|--------|----------|
| Listar usuarios y **asignar o quitar roles** (grupos) | **Usuarios** → **Editar roles** (checkboxes por grupo) |
| **Configurar qué ve cada rol** en el menú y **quién entra a cada URL** | **Menú** → editar opción o **Añadir opción de menú** |
| Ver resumen, **reporte de acceso** y **estadísticas** | Dashboard y enlaces en `/admin-roles/` |
| Consultar **detalle de un rol** (usuarios y opciones de menú que lo usan) | **Roles** → detalle |

**Lo que no está en esa interfaz** (hace falta **Django Admin** `/admin/` con usuario **staff** o **superusuario**, o la consola del servidor):

- Crear o borrar **grupos** nuevos, o marcar permisos Django finos por grupo (`add_lote`, `change_lote`, etc.).
- Marcar usuario como **staff** / **superusuario**, cambiar **contraseña**, o asignar **almacén** al usuario (el formulario web de admin-roles solo cambia **grupos**).
- Ejecutar comandos como `configurar_permisos_roles` o `gestionar_roles` (despliegue / mantenimiento).

En resumen: el administrador operativo puede **dar y quitar acceso por roles y por menú** solo con el navegador; ajustes de **permisos Django al detalle**, **almacén** y **cuentas** siguen en Django Admin o con quien administre el servidor.

---

## 1. Ideas clave (léalo primero)

### 1.1 Dos capas de control

En la práctica conviven **dos mecanismos**:

| Capa | Qué hace | Dónde se ajusta |
|------|-----------|-----------------|
| **Menú y URLs** (`MenuItemRol` + middleware) | Si el usuario entra a una ruta concreta según su **rol (grupo)** | **Administración de roles** → **Menú** (`/admin-roles/menu/`) |
| **Decorador en vistas** (`@requiere_rol(...)`) | Exige que el usuario tenga **al menos uno** de los grupos indicados en el código | Solo cambia con **desarrollo** (no desde pantalla) |

- Para **ampliar o reducir acceso por pantalla** sin tocar código, use **admin-roles → Menú** (ver también `docs/CONTROL_ACCESO_MENU_VERIFICACION.md`).
- Si tras dar acceso en el menú el usuario **sigue bloqueado**, puede ser porque la vista tiene `@requiere_rol` con una lista que **no incluye** su grupo: hay que añadir ese rol en código o dar al usuario un rol que ya esté en la lista.

### 1.2 Rol = grupo de Django

Los “roles” son **grupos** (`auth.Group`). El nombre del grupo debe coincidir **exactamente** con el que esperan el menú y los decoradores (mayúsculas, acentos y espacios).

### 1.3 Superusuario y staff

- **Superusuario** (`is_superuser`): acceso total; ignora restricciones de rol en los decoradores del proyecto.
- **Staff** (`is_staff`): puede entrar al **Django Admin** (`/admin/`). Algunas utilidades del código tratan al staff como “administrador” para ciertos informes (por ejemplo acuse completo vs filtro por almacén).

### 1.4 Almacén asignado al usuario

El modelo de usuario incluye **Almacén asignado** (`User.almacen`). No es un “rol”, pero limita datos (por ejemplo acuses parciales por almacén). Complételo cuando el usuario deba operar siempre en un almacén concreto.

---

## 2. Roles previstos en el sistema

### 2.1 Grupos creados por el comando estándar

El comando `python manage.py gestionar_roles crear` define estos nombres:

- Revisión  
- Almacenero  
- Control Calidad  
- Facturación  
- Supervisión  
- Logística  
- Recepción  
- Conteo  
- Gestor de Inventario  
- **Administrador**

Use **exactamente** estos nombres al asignar grupos desde admin-roles o Django Admin.

### 2.2 Otros nombres que aparecen en el código

Algunas vistas usan grupos **adicionales** que **no** salen en `gestionar_roles crear`. Si un usuario necesita esas pantallas y el grupo no existe, debe **crearse el grupo** en Django Admin (Auth → Groups) con el mismo nombre que en el código:

- **Almacenista**, **Supervisor** — usados en picking  
- **Analista**, **Supervisor** — usados en reportes de salidas y reservas  

Si faltan, los usuarios no podrán pasar el `@requiere_rol` aunque el menú les deje ver el enlace.

---

## 3. Qué puede hacer el administrador desde la aplicación

Quien tenga el rol **Administrador** accede a **Administración de roles** en el menú (URL base: `/admin-roles/`).

### 3.1 Usuarios y grupos

- **Lista de usuarios** → editar usuario → asignar o quitar **grupos (roles)**.  
- Los cambios aplican en el siguiente inicio de sesión o de inmediato según caché del navegador; no suele hacer falta reiniciar el servidor.

### 3.2 Menú por rol (recomendado para ajustes frecuentes)

- **Menú** (`/admin-roles/menu/`): lista de opciones (vistas) y qué **roles** pueden acceder.  
- **Editar** una opción: marcar o desmarcar roles → **Guardar**.  
- **Añadir opción**: registrar un `url_name` nuevo (con namespace si aplica, p. ej. `logistica:lista_propuestas`).

Detalle del funcionamiento del middleware: `docs/CONTROL_ACCESO_MENU_VERIFICACION.md`.

### 3.3 Reporte de acceso y estadísticas

- **Reporte de acceso** y **Estadísticas** en admin-roles ayudan a revisar qué roles tienen qué entradas de menú.

---

## 4. Django Admin (`/admin/`)

Requiere usuario **staff** o superusuario.

- **Usuarios**: grupos, permisos individuales, staff, superusuario, almacén.  
- **Grupos**: crear grupos faltantes (p. ej. Analista) y asignar **permisos Django** si se usan.  

Muchas pantallas del inventario se protegen por **nombre de grupo** (`@requiere_rol`), no solo por permisos CRUD; por tanto, **asignar el grupo correcto** suele ser lo más importante.

---

## 5. Comandos útiles (servidor / despliegue)

Ejecutar desde el directorio del proyecto con el entorno virtual activo:

```bash
# Listar grupos y cuántos usuarios tienen cada uno
python manage.py gestionar_roles listar

# Crear los grupos estándar (si faltan)
python manage.py gestionar_roles crear

# Asignar o quitar un rol
python manage.py gestionar_roles asignar --usuario USUARIO --rol "Gestor de Inventario"
python manage.py gestionar_roles remover --usuario USUARIO --rol "Almacenero"

# Ver grupos y permisos efectivos de un usuario
python manage.py gestionar_roles ver-usuario --usuario USUARIO
```

**Permisos Django por grupo** (tabla `auth`):

```bash
python manage.py configurar_permisos_roles
```

Sobrescribe los permisos de los grupos listados en ese comando según su definición interna. Úselo cuando se actualice el manual de permisos del proyecto, no como sustituto del día a día en producción.

**Menú inicial desde fixtures de código:**

```bash
python manage.py cargar_menu_roles
```

Carga o actualiza registros `MenuItemRol` según el comando. Los ajustes rutinarios del menño se hacen mejor desde **admin-roles → Menú** para no pisar cambios locales.

---

## 6. Buenas prácticas para el administrador

1. **Principio de mínimo privilegio**: un rol operativo (Almacenero, Logística, etc.) y solo los accesos de menú necesarios.  
2. **Probar con un usuario de prueba** con el mismo rol antes de notificar al usuario final.  
3. Si “no puede entrar” pero el menú muestra la opción: revisar **otro rol** en `@requiere_rol` (p. ej. añadir **Analista** al usuario para reportes de salidas).  
4. **Documentar** cambios relevantes (nuevo rol, nuevo acceso masivo) para auditoría.  
5. No eliminar grupos con `gestionar_roles eliminar` sin confirmar que ningún usuario depende de ellos.

---

## 7. Referencias en el código

| Tema | Ubicación |
|------|-----------|
| Decorador principal de roles | `inventario/access_control.py` → `requiere_rol` |
| Decorador alternativo (otro módulo) | `inventario/decorators_roles.py` (algunos módulos legacy; nombres en minúsculas como `administrador`) |
| Vistas admin-roles | `inventario/admin_roles_views.py` |
| URLs admin-roles | `inventario/admin_roles_urls.py` → prefijo `admin-roles/` |
| Definición de menú por defecto | `inventario/management/commands/cargar_menu_roles.py` |
| Permisos sugeridos por rol | `inventario/management/commands/configurar_permisos_roles.py` |
| Usuario y almacén | `inventario/models.py` → `class User` |

---

## 8. Mapeo detallado vista ↔ rol

Para una tabla por pantalla (`url_name`), decorador en código y qué ajustar en el menú, ver **[MAPEO_VISTAS_ROLES.md](./MAPEO_VISTAS_ROLES.md)**.

---

## 9. Resumen rápido

| Necesidad | Acción |
|-----------|--------|
| Dar/quitar un rol a alguien | `/admin-roles/usuarios/` → editar usuario, o Django Admin → Usuario → Grupos |
| Permitir u ocultar una sección del menú | `/admin-roles/menu/` → editar opción → roles permitidos |
| Usuario no entra aunque tenga el menú | Revisar si existe el **grupo** con el nombre exacto que pide la vista (p. ej. Analista) y si `@requiere_rol` lo incluye |
| Permisos CRUD Django por rol | `configurar_permisos_roles` o Django Admin → Grupos |
| Operación ligada a un almacén | Campo **Almacén asignado** en el usuario |

Si necesita un rol nuevo usado solo en menú, basta con crear el grupo y marcarlo en **Menú**. Si además la vista tiene `@requiere_rol`, hay que **añadir ese nombre de grupo en código** o usar un rol ya contemplado.

Consulte **[MAPEO_VISTAS_ROLES.md](./MAPEO_VISTAS_ROLES.md)** para ejemplos (ajuste de existencias, reportes disponibilidad / lote-pedidos, reservas, picking).
