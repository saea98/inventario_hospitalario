# Rol con acceso a Lotes y Reportes de Pedidos

Para que un rol tenga permiso a estas tres vistas:

| Vista (URL) | Nombre de URL (para permisos) |
|-------------|-------------------------------|
| `gestion-inventario/lotes/` | `lista_lotes` |
| `pedidos/reportes/items-no-surtidos/` | `pedidos:reporte_items_no_surtidos` |
| `pedidos/reportes/pedidos-sin-existencia/` | `pedidos:reporte_pedidos_sin_existencia` |

El control de acceso usa **Configuración de Menú por Rol** (`MenuItemRol`): cada opción tiene un `url_name` y varios **roles permitidos** (grupos de Django).

---

## Pasos para crear el rol y asignar permisos

### 1. Crear el grupo (rol) en Django

1. Entra al **Panel de Administración** de Django: `/admin/`
2. Ve a **Autenticación y autorización** → **Grupos**
3. Clic en **Añadir grupo**
4. **Nombre**: por ejemplo `Reportes y Lotes` (o el nombre que quieras para el rol)
5. Guardar

No hace falta asignar “Permisos” del grupo para este acceso; el menú se controla por `MenuItemRol`.

---

### 2. Dar acceso a las tres vistas desde “Configuración de Menú por Rol”

1. En el admin de Django, ve al módulo de **inventario** (o donde esté **Configuración de Menú por Rol** / `MenuItemRol`)
2. Abre cada una de estas **tres** configuraciones de menú y en **Roles permitidos** añade el nuevo grupo:

| Nombre mostrado (aprox.) | url_name en el registro |
|--------------------------|--------------------------|
| **Existencias** | `lista_lotes` |
| **Reporte Items No Surtidos** | `pedidos:reporte_items_no_surtidos` |
| **Reporte Pedidos Sin Existencia** | `pedidos:reporte_pedidos_sin_existencia` |

3. En cada una: en “Roles permitidos”, marca también tu nuevo grupo (ej. `Reportes y Lotes`) y guarda.

---

### 3. Asignar el rol a los usuarios

1. **Autenticación y autorización** → **Usuarios**
2. Edita cada usuario que deba tener este acceso
3. En **Grupos**, asígnale el grupo que creaste (ej. `Reportes y Lotes`)
4. Guardar

---

## Si los reportes de pedidos no aparecen en el menú

Se han añadido al comando de carga de menú. Ejecuta:

```bash
python manage.py cargar_menu_roles
```

Así se crean o actualizan las opciones **Reporte Items No Surtidos** y **Reporte Pedidos Sin Existencia** en `MenuItemRol`. Después, en el admin, añade tu nuevo rol a esas dos y a **Existencias** (`lista_lotes`) como en el paso 2.

---

## Resumen: qué asignar al rol

- **No** son “permisos” de Django (Content types / Permissions).
- **Sí** hay que asignar el **grupo** del rol a los **Roles permitidos** de estas tres configuraciones de menú:
  - Existencias (`lista_lotes`) → `gestion-inventario/lotes/`
  - Reporte Items No Surtidos (`pedidos:reporte_items_no_surtidos`) → `pedidos/reportes/items-no-surtidos/`
  - Reporte Pedidos Sin Existencia (`pedidos:reporte_pedidos_sin_existencia`) → `pedidos/reportes/pedidos-sin-existencia/`

Cuando un usuario tenga el nuevo grupo, podrá entrar a esas tres vistas (y el menú les mostrará las opciones si el front usa la misma configuración de menú por rol).
