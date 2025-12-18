# Manual de Usuario - Gestión de Pedidos (Fase 2.2.1)

## Tabla de Contenidos

1. [Introducción](#introducción)
2. [Roles y Permisos](#roles-y-permisos)
3. [Flujo General del Sistema](#flujo-general-del-sistema)
4. [Crear una Solicitud de Pedido](#crear-una-solicitud-de-pedido)
5. [Validar una Solicitud](#validar-una-solicitud)
6. [Gestionar Propuestas de Surtimiento](#gestionar-propuestas-de-surtimiento)
7. [Preguntas Frecuentes](#preguntas-frecuentes)

---

## Introducción

El módulo de **Gestión de Pedidos** permite a las instituciones de salud solicitar insumos médicos de forma centralizada. El sistema automatiza la generación de propuestas de surtimiento basadas en disponibilidad de inventario, validación de fechas de caducidad y optimización de cantidades.

### Objetivos Principales

- Centralizar solicitudes de insumos médicos
- Automatizar la generación de propuestas de surtimiento
- Validar disponibilidad de productos antes de surtir
- Garantizar que no se surtan productos con fecha de caducidad menor a 60 días
- Permitir correcciones en propuestas antes del surtimiento

---

## Roles y Permisos

### 1. **Solicitante (Personal de Institución)**

**Responsabilidades:**
- Crear nuevas solicitudes de pedido
- Especificar productos y cantidades requeridas
- Proporcionar observaciones adicionales

**Acceso:**
- Crear solicitudes
- Ver historial de sus solicitudes
- Ver estado de propuestas generadas

### 2. **Validador (Personal de Logística/Dirección)**

**Responsabilidades:**
- Revisar solicitudes pendientes
- Aprobar o rechazar items
- Modificar cantidades si es necesario
- Justificar cambios

**Acceso:**
- Ver todas las solicitudes
- Validar solicitudes
- Generar propuestas automáticamente

### 3. **Personal de Almacén**

**Responsabilidades:**
- Revisar propuestas generadas
- Editar lotes asignados si es necesario
- Cambiar cantidades propuestas
- Confirmar surtimiento

**Acceso:**
- Ver propuestas de surtimiento
- Editar propuestas
- Revisar propuestas
- Confirmar surtimiento

---

## Flujo General del Sistema

```
┌─────────────────────────────────────────────────────────────────┐
│                    FLUJO DE GESTIÓN DE PEDIDOS                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. SOLICITANTE                                                  │
│     ├─ Accede a "Gestión de Pedidos"                           │
│     ├─ Crea nueva solicitud                                     │
│     ├─ Selecciona institución y almacén destino                │
│     ├─ Agrega items (productos y cantidades)                   │
│     └─ Envía solicitud                                          │
│                                                                  │
│  2. VALIDADOR                                                    │
│     ├─ Revisa solicitud pendiente                              │
│     ├─ Aprueba o modifica cantidades                           │
│     ├─ Justifica cambios si es necesario                       │
│     └─ Valida solicitud → Sistema genera propuesta             │
│                                                                  │
│  3. SISTEMA (Automático)                                         │
│     ├─ Verifica disponibilidad en inventario                   │
│     ├─ Filtra lotes con caducidad > 60 días                    │
│     ├─ Optimiza cantidades                                      │
│     └─ Genera propuesta de surtimiento                         │
│                                                                  │
│  4. ALMACÉN                                                      │
│     ├─ Revisa propuesta generada                               │
│     ├─ Puede editar lotes y cantidades si es necesario         │
│     ├─ Revisa propuesta                                         │
│     └─ Confirma surtimiento                                     │
│                                                                  │
│  5. SISTEMA (Automático)                                         │
│     ├─ Actualiza inventario                                     │
│     ├─ Registra salida de existencias                          │
│     └─ Marca solicitud como entregada                          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Crear una Solicitud de Pedido

### Paso 1: Acceder al Módulo

1. En el menú lateral, ve a **Gestión Logística**
2. Haz clic en **Gestión de Pedidos**
3. Haz clic en el botón **"Crear Nueva Solicitud"**

### Paso 2: Completar Datos de la Solicitud

En la sección "Datos de la Solicitud", completa:

| Campo | Descripción | Obligatorio |
|-------|-------------|------------|
| **Institución Solicitante** | Selecciona la institución que solicita los insumos | ✅ Sí |
| **Almacén Destino** | Selecciona el almacén donde se entregarán los insumos | ✅ Sí |
| **Fecha de Entrega Programada** | Fecha en que se espera recibir los insumos (mínimo mañana) | ✅ Sí |
| **Observaciones** | Notas adicionales sobre la solicitud | ❌ No |

### Paso 3: Agregar Items

En la sección "Items de la Solicitud":

1. **Selecciona un Producto**: Haz clic en el campo "Producto (CNIS)" y busca por:
   - Código CNIS
   - Descripción del producto
   
2. **Ingresa la Cantidad**: Especifica cuántas unidades necesitas

3. **Agregar más items**: Haz clic en "+ Añadir otro item" si necesitas más productos

### Paso 4: Guardar la Solicitud

1. Revisa que todos los datos sean correctos
2. Haz clic en **"Guardar Solicitud"**
3. El sistema te mostrará un mensaje de confirmación con el folio de la solicitud

**Ejemplo:**
```
Solicitud SOL-20251218-ACB2DF creada con éxito.
```

---

## Validar una Solicitud

### Acceder a Solicitudes Pendientes

1. Ve a **Gestión Logística** → **Gestión de Pedidos**
2. Verás una lista de solicitudes
3. Haz clic en el ícono de **"ojo"** para ver detalles
4. Haz clic en **"Validar Solicitud"** (botón verde)

### Revisar y Validar Items

Para cada item de la solicitud:

1. **Cantidad Solicitada**: Muestra la cantidad original solicitada
2. **Cantidad Aprobada**: Puedes modificar esta cantidad si es necesario
3. **Justificación**: Si cambias la cantidad, explica por qué

### Enviar Validación

1. Revisa todos los cambios
2. Haz clic en **"Validar Solicitud"**
3. El sistema generará automáticamente una propuesta de surtimiento

**¿Qué sucede después?**
- Si todas las cantidades son 0 → Solicitud se rechaza
- Si hay cantidades aprobadas → Se genera propuesta de surtimiento

---

## Gestionar Propuestas de Surtimiento

### Acceder a Propuestas

1. Ve a **Gestión Logística** → **Propuestas de Surtimiento**
2. Verás una lista de propuestas generadas

### Revisar una Propuesta

1. Haz clic en el ícono de **"ojo"** para ver detalles
2. Verás:
   - Datos de la solicitud original
   - Items con cantidades propuestas
   - Lotes asignados para cada item
   - Fechas de caducidad de los lotes

### Editar una Propuesta

Si necesitas cambiar lotes o cantidades:

1. Haz clic en **"Editar Propuesta"** (botón azul)
2. Para cada item puedes:
   - **Cambiar cantidad propuesta**: Modifica el número de unidades
   - **Cambiar lotes asignados**: 
     - Modifica la cantidad de cada lote
     - Marca "Eliminar" para quitar un lote
     - Agrega un nuevo lote si es necesario
3. Haz clic en **"Guardar Cambios"**

### Revisar Propuesta

1. Haz clic en **"Revisar Propuesta"** (botón naranja)
2. Puedes agregar observaciones si es necesario
3. Haz clic en **"Revisar"**

### Confirmar Surtimiento

1. Haz clic en **"Surtir Propuesta"** (botón verde)
2. El sistema:
   - Registrará la salida de inventario
   - Actualizará las cantidades disponibles
   - Marcará la solicitud como entregada

---

## Preguntas Frecuentes

### ¿Qué significa "Cantidad Aprobada"?

Es la cantidad que el validador aprueba para surtir. Puede ser menor que la solicitada si no hay disponibilidad.

### ¿Por qué aparecen productos con "None" en la propuesta?

Esto ocurre si no hay disponibilidad de ese producto en el inventario con fecha de caducidad válida (> 60 días).

### ¿Puedo cambiar una solicitud después de crearla?

No directamente. Si necesitas cambios, contacta al validador para que rechace la solicitud y puedas crear una nueva.

### ¿Qué pasa si no hay suficiente inventario?

El validador puede:
- Reducir la cantidad aprobada
- Rechazar el item completamente
- Justificar el cambio

### ¿Puedo editar una propuesta después de revisarla?

No. Una vez revisada, solo se puede surtir. Si necesitas cambios, contacta al personal de almacén.

### ¿Qué significa "Días para Caducar"?

Es el número de días que faltan para que un lote expire. El sistema solo propone lotes con más de 60 días de vigencia.

### ¿Cómo sé el estado de mi solicitud?

En la lista de solicitudes, verás el estado actual:
- **Pendiente de Validación**: Esperando revisión
- **Validada y Aprobada**: Propuesta generada
- **Rechazada**: No se aprobó
- **En Preparación**: Siendo surtida
- **Preparada para Entrega**: Lista para recoger
- **Entregada**: Completada

---

## Contacto y Soporte

Para problemas o consultas, contacta al equipo de logística:
- **Email**: logistica@imss-bienestar.gob.mx
- **Teléfono**: [Número de contacto]
- **Horario**: Lunes a Viernes, 8:00 AM - 5:00 PM

---

**Versión**: 1.0  
**Última actualización**: Diciembre 2025  
**Desarrollado por**: Equipo de Inventario Hospitalario IMSS-Bienestar
