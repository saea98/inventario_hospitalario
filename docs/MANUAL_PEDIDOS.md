# Manual de Pedidos – Gestión, Propuestas, Picking y Surtimiento

Manual de usuario para el módulo de **Pedidos** del sistema de inventario hospitalario: gestión de solicitudes, carga automática, validación, propuesta de suministro, edición, aprobación, picking, surtimiento completo y cancelaciones.

---

## Tabla de contenidos

1. [Introducción](#1-introducción)
2. [Acceso y rutas](#2-acceso-y-rutas)
3. [Gestión de pedidos](#3-gestión-de-pedidos)
4. [Carga automática (CSV)](#4-carga-automática-csv)
5. [Validación y aprobación de solicitudes](#5-validación-y-aprobación-de-solicitudes)
6. [Propuesta de suministro](#6-propuesta-de-suministro)
7. [Edición de propuesta](#7-edición-de-propuesta)
8. [Aprobación (revisión) de propuesta](#8-aprobación-revisión-de-propuesta)
9. [Picking](#9-picking)
10. [Surtimiento completo](#10-surtimiento-completo)
11. [Cancelaciones](#11-cancelaciones)
12. [Estados y flujo resumido](#12-estados-y-flujo-resumido)
13. [Reportes y auditoría](#13-reportes-y-auditoría)

---

## 1. Introducción

El módulo de **Pedidos** permite:

- Crear y gestionar **solicitudes de pedido** (qué productos y cantidades pide cada institución).
- **Validar** las solicitudes (aprobar o ajustar cantidades).
- Generar de forma automática una **propuesta de suministro** con lotes y ubicaciones.
- **Editar** la propuesta (lotes, ubicaciones, cantidades) antes o después de revisarla.
- **Revisar** la propuesta (aprobación por almacén).
- Realizar el **picking** (recorrido y recolección por ubicaciones).
- Confirmar el **surtimiento completo** (generación de movimientos de inventario).
- **Cancelar** solicitudes o propuestas cuando corresponda.

### Conceptos clave

| Término | Descripción |
|--------|-------------|
| **Solicitud de pedido** | Pedido creado por la institución: folio, institución, almacén destino, fecha de entrega e ítems (producto + cantidad). |
| **Validación** | Revisión por un usuario autorizado: aprobar o rechazar ítems y definir cantidades aprobadas. |
| **Propuesta de suministro** | Asignación automática de lotes y ubicaciones para surtir lo aprobado; incluye reservas de inventario. |
| **Picking** | Proceso de recoger los productos según la propuesta (por ubicación o producto). |
| **Surtimiento** | Confirmación de que se surtió la propuesta; se generan movimientos de inventario y se marcan lotes como surtidos. |

---

## 2. Acceso y rutas

El flujo de pedidos en **Logística** usa estas rutas (prefijo según su instalación, ej. `/logistica/`):

| Acción | Ruta (nombre) |
|--------|----------------|
| Lista de pedidos | `logistica:lista_pedidos` → `/logistica/pedidos/` |
| Crear pedido | `logistica:crear_pedido` → `/logistica/pedidos/crear/` |
| Detalle de pedido | `logistica:detalle_pedido` → `/logistica/pedidos/<uuid>/` |
| Validar pedido | `logistica:validar_pedido` → `/logistica/pedidos/<uuid>/validar/` |
| Editar pedido | `logistica:editar_solicitud` → `/logistica/pedidos/<uuid>/editar/` |
| Cancelar pedido | `logistica:cancelar_solicitud` → `/logistica/pedidos/<uuid>/cancelar/` |
| Lista de propuestas | `logistica:lista_propuestas` → `/logistica/propuestas/` |
| Detalle de propuesta | `logistica:detalle_propuesta` → `/logistica/propuestas/<uuid>/` |
| Editar propuesta | `logistica:editar_propuesta` → `/logistica/propuestas/<uuid>/editar/` |
| Revisar propuesta | `logistica:revisar_propuesta` → `/logistica/propuestas/<uuid>/revisar/` |
| Picking | `logistica:picking_propuesta` → `/logistica/propuestas/<uuid>/picking/` |
| Surtir propuesta | `logistica:surtir_propuesta` → `/logistica/propuestas/<uuid>/surtir/` |
| Cancelar propuesta | `logistica:cancelar_propuesta` → `/logistica/propuestas/<uuid>/cancelar/` |
| Eliminar propuesta | `logistica:eliminar_propuesta` → `/logistica/propuestas/<uuid>/eliminar/` |

Desde el menú: **Logística → Gestión de Pedidos** (lista de solicitudes) y desde ahí a detalle, validar, editar o cancelar. Las propuestas se abren desde el detalle del pedido o desde **Logística → Propuestas** (si existe en el menú).

---

## 3. Gestión de pedidos

### 3.1 Lista de solicitudes

- **Vista**: lista de todas las solicitudes con folio, institución, almacén destino, fecha de solicitud, estado.
- **Filtros**: estado, rango de fechas, institución, folio.
- **Acciones**: ver detalle, validar (si está pendiente), editar, cancelar (si está pendiente o validada).

### 3.2 Crear solicitud

1. Ir a **Crear pedido** (o **Nueva solicitud**).
2. Completar:
   - **Institución solicitante**
   - **Almacén destino**
   - **Fecha de entrega programada**
   - **Observaciones** (opcional)
3. Añadir ítems:
   - **Producto (clave CNIS)**: búsqueda en catálogo.
   - **Cantidad solicitada**: entero mayor a 0.
4. Opcional: usar **Carga automática por CSV** (ver sección 4).
5. **Guardar**: se genera un folio único (ej. `SOL-YYYYMMDD-XXXXXX`).

La solicitud queda en estado **Pendiente de validación** hasta que un usuario autorizado la valide.

### 3.3 Detalle de solicitud

- Encabezado: folio, institución, almacén, fechas, estado.
- Ítems: producto, cantidad solicitada, cantidad aprobada (tras validación), justificación si hubo cambio.
- Si existe propuesta: enlace al detalle de la propuesta y a editar/revisar/picking/surtir según estado.
- Si la solicitud está validada: se muestran ítems a surtir (cantidad aprobada > 0) e ítems sin existencia (cantidad aprobada = 0).

### 3.4 Editar solicitud

- Permitido en estados **PENDIENTE** y **VALIDADA**.
- Se puede cambiar encabezado (institución, almacén, fecha de entrega, observaciones) e ítems (añadir, quitar, cambiar cantidades).
- **Si está PENDIENTE**: solo se guardan cambios; la solicitud sigue pendiente.
- **Si está VALIDADA**:
  - Se cancela la propuesta actual (se liberan reservas).
  - Se guardan cambios en la solicitud.
  - Se valida disponibilidad de los ítems con cantidad aprobada > 0.
  - Si hay disponibilidad, se genera una **nueva propuesta** automáticamente.

Si no hay disponibilidad suficiente para los ítems aprobados, el sistema informa el error y no genera propuesta; la solicitud sigue validada pero sin propuesta hasta corregir datos o disponibilidad.

---

## 4. Carga automática (CSV)

Al **crear** una solicitud se puede cargar un archivo CSV para añadir muchos ítems de una vez.

### 4.1 Formato del CSV

- **Columnas requeridas**:
  - `CLAVE`: clave CNIS del producto.
  - `CANTIDAD SOLICITADA`: número entero (cantidad a solicitar).
- Codificación: UTF-8 (con o sin BOM), Latin-1 o CP1252.
- Separador: coma (CSV estándar).

Ejemplo:

```csv
CLAVE,CANTIDAD SOLICITADA
060.506.4492,100
123.456.7890,50
```

### 4.2 Comportamiento

- Se usa el botón/opción **Cargar CSV** (o equivalente) en la pantalla de creación.
- El sistema:
  - Valida que cada **CLAVE** exista en el catálogo; si no existe, se registra error y se omite la fila.
  - Valida que **CANTIDAD SOLICITADA** sea un número válido; si no, se omite y se advierte.
- No se valida disponibilidad en este paso; la disponibilidad se resuelve al **validar** la solicitud y al **generar la propuesta**.
- Las filas válidas se añaden como ítems al formulario; luego el usuario completa institución, almacén, fecha y guarda la solicitud normalmente.

Errores típicos: “Clave no existe”, “Cantidad no válida”. Revisar el archivo y volver a cargar si es necesario.

---

## 5. Validación y aprobación de solicitudes

Solo las solicitudes en estado **PENDIENTE** pueden ser validadas.

### 5.1 Quién valida

Usuario con permisos de validación (por ejemplo, logística o dirección).

### 5.2 Pantalla de validación

- Se muestra cada ítem con cantidad solicitada.
- Por ítem se puede:
  - **Aprobar**: mantener o cambiar la cantidad (campo “Cantidad aprobada”).
  - **Rechazar**: poner cantidad aprobada en 0.
  - **Justificación**: texto opcional si se reduce o rechaza.

### 5.3 Reglas al guardar

- Si **todas** las cantidades aprobadas son 0 → la solicitud pasa a **RECHAZADA**.
- Si **alguna** cantidad aprobada > 0:
  - La solicitud pasa a **VALIDADA**.
  - Por cada ítem con cantidad aprobada > 0 se comprueba disponibilidad:
    - Si no hay ninguna existencia → se excluye del surtido (cantidad aprobada se pone en 0) y se registra en log.
    - Si hay disponibilidad parcial → se mantiene la cantidad aprobada; la propuesta asignará lo disponible y buscará en otros lotes/ubicaciones.
  - Se genera automáticamente la **propuesta de suministro** (reservas y asignación de lotes/ubicaciones).

Mensajes típicos: “Solicitud validada. Propuesta generada con N producto(s)” o advertencia de ítems excluidos por falta de disponibilidad.

---

## 6. Propuesta de suministro

La propuesta se **genera automáticamente** al validar la solicitud (y, si aplica, al editar una solicitud validada y guardar con nueva propuesta).

### 6.1 Qué contiene

- **Propuesta de pedido**: asociada 1:1 a la solicitud.
- **Ítems de propuesta**: por cada ítem de solicitud con cantidad aprobada > 0:
  - Producto, cantidad solicitada, cantidad disponible, cantidad propuesta.
  - **Lotes asignados** (`LoteAsignado`): lote, ubicación (`LoteUbicacion`), cantidad asignada y reserva en inventario.

### 6.2 Cómo se genera (resumen técnico)

- Solo ítems con `cantidad_aprobada > 0`.
- Se buscan lotes con:
  - Mismo producto.
  - Fecha de caducidad vigente (por ejemplo ≥ hoy).
  - Estado activo.
  - Existencia en ubicaciones (considerando almacén central y almacén destino).
- Se prioriza por caducidad y se asignan cantidades hasta cubrir lo aprobado; se crean reservas (`cantidad_reservada` / asignaciones no surtidas).

### 6.3 Estados de la propuesta

- **GENERADA**: recién creada; se puede editar, revisar o cancelar.
- **REVISADA**: el almacén la aprobó; se puede ir a picking o surtir.
- **EN_SURTIMIENTO**: en proceso de picking/surtido.
- **SURTIDA**: surtimiento confirmado; movimientos generados.
- **PARCIAL** / **NO_DISPONIBLE** / **CANCELADA**: según reglas del negocio.

Desde el **detalle del pedido** se accede al detalle de la propuesta y a: Editar, Revisar, Picking, Surtir, Cancelar, Eliminar (según estado y permisos).

---

## 7. Edición de propuesta

Permite ajustar **lotes, ubicaciones y cantidades** antes (y en algunos casos después) del surtimiento.

### 7.1 Cuándo se puede editar

Estados en los que la propuesta es editable: **GENERADA**, **REVISADA**, **EN_SURTIMIENTO**, **SURTIDA** (este último para correcciones).

### 7.2 Qué se puede hacer

- **Por ítem**:
  - Cambiar **ubicación/lote** (selector por producto: lote + ubicación con cantidad disponible).
  - Cambiar **cantidad** (límite: disponible en esa ubicación + cantidad ya asignada al ítem).
  - **Eliminar** ítem de la propuesta (libera reservas de ese ítem).
- **Guardar por renglón**: “Guardar este renglón” aplica solo a ese ítem (libera reservas previas del ítem y vuelve a reservar según lo elegido).
- **Guardar y terminar**: guarda todos los cambios pendientes; si hay ítems modificados sin guardar, el sistema puede pedir guardar por ítem antes.

La disponibilidad mostrada en el selector usa la **reserva real** (suma de asignaciones no surtidas), no solo el campo `cantidad_reservada`, para evitar mensajes incorrectos de “cantidad insuficiente”.

### 7.3 Edición cuando ya está surtida

En estado **SURTIDA** (y REVISADA/EN_SURTIMIENTO) está disponible la opción **Editar Propuesta (corrección)** para ajustar o añadir ítems/lotes si se detecta un error después del surtimiento.

---

## 8. Aprobación (revisión) de propuesta

Es el paso en el que el **almacén** da por buena la propuesta y la deja lista para picking y surtimiento.

### 8.1 Cuándo

Solo en estado **GENERADA**.

### 8.2 Acción

- Ir a **Revisar propuesta** (desde detalle de la propuesta).
- Confirmar revisión.
- El sistema:
  - Marca **fecha y usuario de revisión**.
  - Cambia estado a **REVISADA**.

A partir de aquí se puede:
- **Picking**: ver hoja de surtido e ir marcando lo recogido.
- **Surtir**: confirmar surtimiento completo y generar movimientos.

---

## 9. Picking

El picking es el proceso de **recorrido y recolección** de los productos según la propuesta.

### 9.1 Cuándo está disponible

Propuesta en estado **REVISADA** o **EN_SURTIMIENTO**.

### 9.2 Pantalla de picking

- Listado de ítems ordenados por **ubicación** (u otro criterio configurado: producto, cantidad).
- Por cada ítem: producto, lote, ubicación, cantidad a recoger.
- Acciones:
  - **Marcar como recogido** por ítem/lote.
  - **Imprimir hoja de surtido** (PDF).
  - **Exportar a Excel** (lista para impresión o uso externo).
- Opcional: corrección de lote/ubicación o cantidad desde la misma pantalla (según permisos y si está implementado).

### 9.3 Flujo recomendado

1. Revisar propuesta (aprobación almacén).
2. Imprimir o exportar hoja de surtido.
3. Realizar el recorrido y recoger productos.
4. Marcar ítems como recogidos en la pantalla de picking.
5. Cuando todo esté recogido, ir a **Surtir propuesta** para cerrar el surtimiento.

---

## 10. Surtimiento completo

Confirma que la propuesta fue surtida y **genera los movimientos de inventario** y marca las asignaciones como surtidas.

### 10.1 Cuándo

Propuesta en estado **REVISADA** (habitualmente después del picking).

### 10.2 Acción

- Ir a **Surtir propuesta** (desde detalle de la propuesta).
- Confirmar surtimiento.

### 10.3 Qué hace el sistema

1. **Genera movimientos de inventario** por cada lote/ubicación y cantidad surtida (salidas), usando existencias reales en `LoteUbicacion` para evitar cantidades negativas.
2. Si en ese paso faltara cantidad (por ejemplo, desfase entre lo reservado y lo real), el sistema devuelve error y **no** marca la propuesta como surtida ni aplica cambios.
3. Si todo es correcto:
   - Marca cada **LoteAsignado** como surtido (fecha de surtimiento).
   - Actualiza estado de la propuesta a **EN_SURTIMIENTO** y luego a **SURTIDA**.
   - Registra usuario y fecha de surtimiento.

Mensaje típico: “Propuesta surtida exitosamente”. A partir de ahí la solicitud queda con propuesta **SURTIDA** y los movimientos de inventario ya generados.

---

## 11. Cancelaciones

### 11.1 Cancelar solicitud

- **Estados permitidos**: PENDIENTE, VALIDADA.
- **Efectos**:
  - Si existe propuesta: primero se **cancela/libera la propuesta** (liberación de todas las reservas).
  - La propuesta se elimina.
  - La solicitud pasa a estado **CANCELADA**.

Ruta: desde detalle del pedido → **Cancelar solicitud** → confirmar.

### 11.2 Cancelar propuesta (liberar reservas)

- **Estados permitidos**: GENERADA, REVISADA, EN_SURTIMIENTO.
- **Efecto**: se liberan todas las reservas de la propuesta y su estado vuelve a **GENERADA** (queda editable); la solicitud sigue **VALIDADA**.
- Uso: corregir asignaciones sin cancelar el pedido; después se puede editar de nuevo la propuesta y volver a revisar/surtir.

Ruta: desde detalle de la propuesta → **Cancelar propuesta** (o “Liberar reservas”) → confirmar.

### 11.3 Eliminar propuesta

- **Efecto**: rollback de reservas, registro de movimientos si aplica y **eliminación** del registro de la propuesta. La solicitud queda validada pero sin propuesta; puede generarse una nueva editando la solicitud y guardando (o según flujo configurado).
- Requiere permisos (por ejemplo staff o grupo Almacenero).

Ruta: desde detalle de la propuesta → **Eliminar propuesta** → confirmar.

---

## 12. Estados y flujo resumido

### 12.1 Solicitud de pedido

| Estado | Descripción |
|--------|-------------|
| PENDIENTE | Creada; pendiente de validación. |
| VALIDADA | Aprobada; tiene o puede tener propuesta. |
| RECHAZADA | Todas las cantidades aprobadas en 0. |
| EN_PREPARACION / PREPARADA / ENTREGADA | Según flujo de entrega. |
| CANCELADA | Cancelada por el usuario. |

### 12.2 Propuesta de suministro

| Estado | Descripción |
|--------|-------------|
| GENERADA | Recién generada; editable; se puede revisar o cancelar. |
| REVISADA | Aprobada por almacén; se puede hacer picking y surtir. |
| EN_SURTIMIENTO | En proceso de picking/surtido. |
| SURTIDA | Surtimiento confirmado; movimientos generados. |
| PARCIAL / NO_DISPONIBLE / CANCELADA | Según reglas del negocio. |

### 12.3 Flujo típico

```
Crear solicitud (manual o CSV)
    → PENDIENTE
Validar solicitud (aprobar ítems/cantidades)
    → VALIDADA + Propuesta GENERADA
Opcional: Editar propuesta (lotes/ubicaciones/cantidades)
    → Sigue GENERADA
Revisar propuesta (almacén aprueba)
    → REVISADA
Picking (recoger por ubicaciones)
    → Sigue REVISADA o EN_SURTIMIENTO
Surtir propuesta (confirmar y generar movimientos)
    → SURTIDA
```

Cancelaciones:

- **Solo propuesta**: Cancelar propuesta → reservas liberadas, propuesta en GENERADA.
- **Todo el pedido**: Cancelar solicitud → se libera/elimina propuesta y solicitud pasa a CANCELADA.

---

## 13. Reportes y auditoría

El módulo de pedidos suele incluir (según instalación):

- **Reporte de pedidos**: listado/filtros por fechas, institución, estado.
- **Reporte de errores de pedidos**: claves no existentes, cantidades inválidas, sin existencia.
- **Reporte de reservas**: reservas activas por producto/lote/ubicación (alineado con la “reserva real” usada en edición de propuesta).
- **Reporte de ítems no surtidos / claves sin existencia**: para seguimiento de faltantes.
- **Auditoría de propuestas / surtido**: trazabilidad de quién generó, revisó y surtió cada propuesta.

Las rutas exactas dependen de la configuración de reportes (por ejemplo bajo **Reportes** o **Logística**).

---

## Resumen rápido por rol

| Rol | Acciones principales |
|-----|----------------------|
| **Solicitante** | Crear solicitud, carga CSV, ver detalle y estado. |
| **Validador** | Validar solicitud (aprobar/rechazar ítems y cantidades); se genera la propuesta. |
| **Almacén** | Ver/editar propuesta, revisar propuesta, picking, surtir propuesta, cancelar/eliminar propuesta. |

Para permisos concretos (grupos, staff, nombres de URLs) consultar la configuración del proyecto y, si existe, documentación de roles y permisos.
