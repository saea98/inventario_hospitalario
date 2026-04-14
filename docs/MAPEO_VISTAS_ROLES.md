# Mapeo: vistas → roles requeridos (`url_name`)

Este documento ayuda al **administrador** a saber qué **grupo (rol)** debe tener un usuario para usar cada pantalla. Complementa [GUIA_PERMISOS_Y_ROLES.md](./GUIA_PERMISOS_Y_ROLES.md).

---

## Cómo interpretar el acceso (dos reglas)

1. **Decorador `@requiere_rol(...)`** en la vista  
   El usuario debe pertenecer a **al menos uno** de los grupos listados (o ser **superusuario**). Si no, se redirige al dashboard con mensaje. Los nombres deben coincidir **exactamente** con el grupo en Django (mayúsculas y acentos).

2. **Middleware + `MenuItemRol`**  
   Si existe en base de datos una fila **activa** con ese `url_name`, solo los **roles marcados** en esa fila pueden entrar (salvo superusuario).  
   - Si **no** hay fila para esa URL → **cualquier usuario autenticado** puede abrirla si conoce el enlace (a menos que la vista tenga `@requiere_rol`).  
   - Para **cerrar** el acceso o **abrirlo** sin tocar código: `/admin-roles/menu/` (ver [CONTROL_ACCESO_MENU_VERIFICACION.md](./CONTROL_ACCESO_MENU_VERIFICACION.md)).

En la práctica: **se cumplen las dos condiciones** cuando ambas aplican (primero menú, luego decorador al ejecutar la vista).

---

## Roles estándar vs roles “extra”

- **`gestionar_roles crear`** crea: Revisión, Almacenero, Control Calidad, Facturación, Supervisión, Logística, Recepción, Conteo, Gestor de Inventario, **Administrador**.
- El código también exige a veces: **Almacenista**, **Supervisor**, **Analista**. Esos grupos hay que **crearlos en Django Admin → Grupos** si aún no existen, y asignarlos a quien corresponda.

---

## A. Vistas con `@requiere_rol` fijo en código

Si el usuario no tiene uno de estos roles, **no entrará** aunque el menú lo muestre.

### A.1 `access_control.requiere_rol` (nombres con mayúscula típica)

| Módulo / archivo | Vista (función) | `url_name` (referencia) | Roles permitidos (uno basta) |
|------------------|-------------------|-------------------------|------------------------------|
| `views.py` | `lista_instituciones` | `lista_instituciones` | Administrador |
| `views_entrada_salida.py` | `entrada_almacen_paso1` | `entrada_almacen_paso1` | Almacenero, Supervisión, Control Calidad |
| `views_ubicaciones_almacen.py` | `lista_ubicaciones_almacen` | `lista_ubicaciones_almacen` | Administrador, Gestor de Inventario, Almacenero, Supervisión |
| `views_ubicaciones_almacen.py` | `crear_ubicacion_almacen` | `crear_ubicacion_almacen` | (mismos) |
| `views_ubicaciones_almacen.py` | `editar_ubicacion_almacen` | `editar_ubicacion_almacen` | (mismos) |
| `views_conteo_fisico_v2.py` | Solo **`buscar_lote_conteo`** | `logistica:buscar_lote_conteo` | Almacenero, Administrador, Gestor de Inventario, Supervisión |
| `views_conteo_fisico_v2.py` | Resto del flujo (seleccionar ubicación/lote, **capturar conteo**, historial, exportar, etc.) | `logistica:seleccionar_ubicacion_conteo`, `logistica:capturar_conteo_lote`, … | **Solo `@login_required` o sin decorador de rol** → control principalmente por **menú** y sesión; conviene registrar cada `url_name` en `MenuItemRol` con los mismos roles operativos. |
| `views_dashboard_conteos.py` | `dashboard_conteos`, exportaciones | `logistica:dashboard_conteos`, `logistica:exportar_conteos_excel`, `logistica:exportar_conteos_pdf` | (mismos) |
| `admin_roles_views.py` | Todo el módulo admin-roles | `admin_roles:*` | Administrador |

**Nota entrada al almacén:** solo **paso 1** tiene `@requiere_rol`. Los pasos siguientes usan `@login_required`; el acceso real depende mucho del **menú** (`MenuItemRol`) y de no compartir URL sin protección. Conviene tener registrada en menú toda la cadena `entrada_almacen_*` con los mismos roles operativos.

### A.2 `decorators_roles.requiere_rol` (reportes de salidas y picking)

Mismo comportamiento (incluye comprobación de login). Usado en:

| Archivo | Vistas | Roles |
|---------|--------|--------|
| `views_reportes_salidas.py` | `reporte_general_salidas`, `analisis_distribuciones`, `analisis_temporal` | Administrador, Gestor de Inventario, **Analista** |
| `views_reportes_salidas.py` | `reporte_salidas_surtidas`, `aplicar_salida_surtida`, `movimientos_surtimiento`, `exportar_salidas_surtidas_excel` | Administrador, Gestor de Inventario, Analista, **Supervisor** |
| `views_reportes_salidas.py` | `reporte_reservas`, `exportar_reservas_excel` | Administrador, Gestor de Inventario, Analista, Supervisor |
| `views_reportes_salidas.py` | **`liberar_reserva`** (POST, AJAX) | Administrador, Gestor de Inventario, **Supervisor** — **sin Analista** |
| `picking_views.py` | `dashboard_picking`, `picking_propuesta` | **Almacenista**, Administrador, Gestor de Inventario |
| `picking_views.py` | `monitor_picking` | Almacenista, Administrador, Gestor de Inventario, Supervisor |

**Rutas URL (app `reportes_salidas`):**  
`reportes/salidas/general/`, `distribuciones/`, `temporal/`, `surtidas/`, `reservas/`, etc. — nombres: `reportes_salidas:reporte_general`, `reportes_salidas:reporte_reservas`, `reportes_salidas:liberar_reserva`, …

**Picking:** `picking/` → `picking:dashboard`; picking de propuesta: `logistica:picking_propuesta`.

---

## B. Ejemplos que pidió negocio (solo `@login_required` en código)

Estas vistas **no** tienen `@requiere_rol`. Quién entra depende casi solo de **`MenuItemRol`** (y de si la URL está registrada).

| Funcionalidad | Ruta típica | `url_name` | Qué hacer en administración |
|---------------|-------------|------------|-----------------------------|
| **Ajustar existencias (cantidad en lote)** | `…/gestion-inventario/lotes/<id>/ajustar-cantidad/` | `ajustar_cantidad_lote` | En **admin-roles → Menú**: crear o editar opción con ese `url_name` y marcar los roles que puedan ajustar (p. ej. Gestor de Inventario, Supervisión). Si **no** hay fila, cualquier usuario logueado con el enlace podría entrar. |
| Lista / detalle lotes (Fase 2.3) | `…/gestion-inventario/lotes/` | `lista_lotes`, `detalle_lote` | Igual: `MenuItemRol` por URL. El comando `cargar_menu_roles` deja `lista_lotes` con Almacenero, Supervisión, Administrador, Gestor de Inventario. |
| **Disponibilidad vs reservas (por lote)** | `…/reportes-disponibilidad/disponibilidad-lotes/` | `reportes:reporte_disponibilidad_lotes` (si aplica namespace; si no, `reporte_disponibilidad_lotes`) | Añadir/editar en menú y asignar roles. |
| **Lotes en pedidos (trazabilidad clave/lote/pedido)** | `…/reportes-disponibilidad/lote-pedidos/` | `reportes:reporte_lote_pedidos` (o `reporte_lote_pedidos`) | Igual. |
| Reportes de pedidos (items no surtidos, etc.) | `…/pedidos/reportes/…` | `pedidos:reporte_items_no_surtidos`, etc. | Ver [ROL_VISTAS_LOTES_Y_REPORTES_PEDIDOS.md](./ROL_VISTAS_LOTES_Y_REPORTES_PEDIDOS.md). |
| Flujo completo **logística / pedidos / propuestas** | `logistica:…` | `logistica:lista_pedidos`, `logistica:lista_propuestas`, `logistica:editar_propuesta`, … | Solo `@login_required` en `pedidos_views`; control por menú. |

**Cómo ver el `url_name` exacto en su instalación**

- Pantalla **admin-roles → Reporte de acceso** (lista `MenuItemRol`), o  
- Django shell: `python manage.py shell` → `from django.urls import resolve; print(resolve("/ruta/completa/").url_name)` (y `namespace` si aplica).

---

## C. Menú por defecto (`cargar_menu_roles`)

Solo como **referencia**; en producción puede diferir si ya editaron el menú en `/admin-roles/menu/`.

| Nombre mostrado (aprox.) | `url_name` | Roles en el comando |
|--------------------------|------------|---------------------|
| Dashboard | `dashboard` | Todos los roles estándar del comando |
| Existencias | `lista_lotes` | Almacenero, Supervisión, Administrador, Gestor de Inventario |
| Entrada al almacén | `entrada_almacen_paso1` | Almacenero, Supervisión, Administrador |
| Salidas (proveeduría) | `proveeduria_paso1` | Almacenero, Supervisión, Administrador |
| Gestión de pedidos | `logistica:lista_pedidos` | Revisión, Supervisión, Administrador |
| Propuestas surtimiento | `logistica:lista_propuestas` | Almacenero, Supervisión, Administrador |
| Reportes items no surtidos / sin existencia | `pedidos:…` | Supervisión, Administrador |
| Reportes de salidas (entrada menú) | `reportes_salidas:reporte_general` | Supervisión, Administrador |
| Picking | `picking:dashboard` | Almacenero, Supervisión, Administrador |
| Inventario (movimientos) | `lista_movimientos` | Gestor de Inventario, Supervisión, Administrador |
| … | … | … |

**Discrepancia importante:** en el comando, **Picking** permite *Almacenero*, pero la vista `picking_propuesta` exige **Almacenista** (u otros en lista). Un usuario solo *Almacenero* podría ver el menú y fallar al abrir el picking: hay que darle **Almacenista** o alinear código/menú en un futuro cambio.

---

## D. Superusuario y staff

- **Superusuario:** pasa cualquier `@requiere_rol` y cualquier `MenuItemRol`.
- **Staff:** no sustituye al grupo *Administrador* en `@requiere_rol`, salvo lógica puntual en algunas pantallas (p. ej. acuse PDF completo vs filtro por almacén).

---

## E. Mantenimiento del documento

Este mapeo se obtuvo del código en el repositorio. Si añaden vistas o decoradores, pueden:

- Buscar `@requiere_rol` en `inventario/*.py`, o  
- Usar / mejorar `python manage.py validar_control_acceso` si está disponible en su rama.

**Última revisión:** generada a partir de decoradores en `access_control`, `decorators_roles`, `views_reportes_salidas`, `picking_views`, `views_entrada_salida`, `views_ubicaciones_almacen`, `views_conteo_fisico_v2`, `views_dashboard_conteos`, `admin_roles_views`, y rutas en `urls_inventario`, `urls_reportes_salidas`, `urls_fase2`, `urls_picking`, `reportes_urls`.
