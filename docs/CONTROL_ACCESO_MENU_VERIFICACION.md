# Verificación: control de acceso desde admin-roles/menu/

El acceso a las vistas se controla **solo con la configuración de menú** en **admin-roles/menu/** (y opcionalmente desde Django Admin → MenuItemRol). No hace falta modificar código para dar o quitar acceso a un rol.

---

## 1. Cómo funciona

1. **Middleware** (`inventario/middleware.py` → `ControlAccesoRolesMiddleware`):
   - En cada petición obtiene el **nombre de la URL** con `resolve(request.path_info).url_name` (ej: `lista_lotes`, `pedidos:reporte_items_no_surtidos`).
   - Busca en **MenuItemRol** un registro con ese `url_name` y `activo=True`.
   - Si existe: comprueba si el usuario tiene alguno de los **roles permitidos** de esa opción (`puede_ver_usuario`). Si no tiene ninguno → redirige al dashboard con mensaje de sin permiso.
   - Si **no** existe ninguna opción con ese `url_name` → se permite el acceso (comportamiento por defecto para URLs no registradas).

2. **Configuración de menú** (`admin-roles/menu/`):
   - **Lista**: ves todas las opciones (vistas) y qué roles tienen acceso.
   - **Editar**: en cada opción puedes cambiar los **roles permitidos** y activar/desactivar. Los cambios se aplican de inmediato; el middleware usa siempre la base de datos.
   - **Crear** (Añadir opción de menú): puedes registrar una **nueva vista** sin tocar código. Solo necesitas:
     - **Nombre de URL (url_name)**: debe ser exactamente el que devuelve Django para esa ruta (con namespace si aplica, ej: `pedidos:reporte_items_no_surtidos`).
     - Identificador de menú, nombre mostrado, icono, orden y los roles que pueden acceder.

3. **Dónde se usa el `url_name`**
   - Las URLs con `include()` y `app_name` tienen nombre con namespace, ej: `pedidos:reporte_items_no_surtidos`.
   - Las URLs bajo `gestion-inventario/` (include de `urls_inventario`) no tienen namespace, ej: `lista_lotes`.
   - Para saber el `url_name` de una ruta puedes revisar el `name=` en el `path()` correspondiente y, si está dentro de un `include` con `app_name`, prefijar con `app_name:`.

---

## 2. Comprobar que la implementación es correcta

- **Asignar/quitar roles desde el menú**: en admin-roles/menu/ → Editar en una opción → marcar o desmarcar roles → Guardar. Un usuario con ese rol debe poder o no poder entrar a la vista según corresponda (sin reiniciar servidor).
- **Nueva vista sin tocar código**: admin-roles/menu/ → Añadir opción de menú → rellenar **Nombre de URL** con el `url_name` real de la vista → asignar roles → Crear. Esa vista quedará protegida por el middleware para los roles elegidos.
- **URLs excluidas del control**: el middleware no aplica control a `login`, `logout`, `dashboard`, `admin:login`, `admin:logout`, `admin:index`. El resto de URLs se controlan si tienen un MenuItemRol activo con ese `url_name`.

---

## 3. Resumen

| Qué quieres hacer | Dónde |
|-------------------|--------|
| Que un rol tenga acceso a una vista | admin-roles/menu/ → buscar la opción (por nombre o URL) → Editar → marcar el rol → Guardar |
| Quitar acceso a un rol | admin-roles/menu/ → Editar la opción → desmarcar el rol → Guardar |
| Registrar una vista nueva (sin código) | admin-roles/menu/ → Añadir opción de menú → rellenar url_name y datos → asignar roles → Crear |
| Ver qué roles tienen acceso a qué | admin-roles/menu/ (lista) o admin-roles/reporte-acceso/ |

No es necesario modificar vistas ni el comando `cargar_menu_roles` para cambiar accesos; solo la configuración en admin-roles/menu/ (o en Django Admin → MenuItemRol).
