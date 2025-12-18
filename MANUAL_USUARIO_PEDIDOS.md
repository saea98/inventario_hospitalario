# Manual de Usuario: Gestión de Pedidos

## Introducción

La **Gestión de Pedidos** es el módulo de la Fase 2.2.1 que permite a las instituciones de salud solicitar insumos médicos al almacén central y a los administradores validar y aprobar estas solicitudes.

## Acceso al Módulo

1. Inicia sesión en el sistema con tu usuario
2. En el menú lateral, selecciona **Logística**
3. Haz clic en **Gestión de Pedidos**

## Funcionalidades Principales

### 1. Ver Lista de Solicitudes

La pantalla principal muestra todas las solicitudes de pedido con la siguiente información:

| Campo | Descripción |
|-------|-------------|
| **Folio** | Identificador único de la solicitud (ej: SOL-20231215-ABC123) |
| **Institución Solicitante** | Nombre de la institución que solicita |
| **Almacén Destino** | Almacén donde se entregarán los productos |
| **Fecha de Solicitud** | Cuándo se creó la solicitud |
| **Estado** | Estado actual de la solicitud |
| **Acciones** | Botones para ver detalles o validar |

#### Filtros Disponibles

Puedes filtrar las solicitudes por:
- **Estado**: Pendiente, Validada, Rechazada, En Preparación, Preparada, Entregada, Cancelada
- **Fecha Inicio**: Desde cuándo buscar
- **Fecha Fin**: Hasta cuándo buscar
- **Institución**: Nombre de la institución

### 2. Crear Nueva Solicitud

**Paso 1: Acceder al Formulario**
- Haz clic en el botón **"Nueva Solicitud"** (esquina superior derecha)

**Paso 2: Completar Datos Principales**
- **Institución Solicitante**: Selecciona la institución que solicita
- **Almacén Destino**: Selecciona el almacén donde se entregarán los productos
- **Fecha de Entrega Programada**: Selecciona la fecha en que se necesitan los productos
- **Observaciones**: (Opcional) Agrega notas adicionales

**Paso 3: Agregar Items**
- En la sección "Items de la Solicitud", completa:
  - **Producto (CNIS)**: Selecciona el producto del catálogo
  - **Cantidad Solicitada**: Ingresa la cantidad necesaria
- Para agregar más items, haz clic en **"Añadir otro item"**

**Paso 4: Guardar**
- Haz clic en **"Guardar Solicitud"**
- El sistema generará un folio automático

### 3. Ver Detalle de Solicitud

Al hacer clic en el botón de ojo (👁️) en la lista:

- Verás toda la información de la solicitud
- Se mostrarán los items solicitados con sus cantidades
- Si ya fue validada, verás las cantidades aprobadas y justificaciones

### 4. Validar Solicitud

**Quién puede validar**: Usuarios con permisos de administrador

**Paso 1: Acceder a la Validación**
- En la lista, haz clic en el botón de validación (✓) para solicitudes en estado PENDIENTE
- O desde el detalle, haz clic en **"Validar Solicitud"**

**Paso 2: Revisar Items**
Para cada item, puedes:
- **Aprobar cantidad completa**: Mantén la cantidad solicitada
- **Reducir cantidad**: Si no hay disponibilidad suficiente
- **Rechazar item**: Establece cantidad aprobada en 0
- **Agregar justificación**: Explica por qué cambió la cantidad

**Paso 3: Guardar Validación**
- Haz clic en **"Guardar Validación"**
- El sistema actualizará automáticamente el estado:
  - Si se aprueban items: Estado = **VALIDADA**
  - Si se rechazan todos: Estado = **RECHAZADA**

## Estados de la Solicitud

| Estado | Descripción | Acciones Disponibles |
|--------|-------------|----------------------|
| **PENDIENTE** | Solicitud creada, esperando validación | Validar, Ver Detalle |
| **VALIDADA** | Solicitud aprobada, lista para surtimiento | Ver Detalle |
| **RECHAZADA** | Solicitud rechazada por falta de disponibilidad | Ver Detalle |
| **EN_PREPARACION** | Se está preparando el surtimiento | Ver Detalle |
| **PREPARADA** | Surtimiento listo para entrega | Ver Detalle |
| **ENTREGADA** | Solicitud completada | Ver Detalle |
| **CANCELADA** | Solicitud cancelada por el usuario | Ver Detalle |

## Flujo Típico de una Solicitud

```
1. Crear Solicitud (Estado: PENDIENTE)
        ↓
2. Validar Solicitud (Estado: VALIDADA o RECHAZADA)
        ↓
3. Preparar Surtimiento (Estado: EN_PREPARACION)
        ↓
4. Confirmar Preparación (Estado: PREPARADA)
        ↓
5. Entregar (Estado: ENTREGADA)
```

## Consejos Útiles

### Para Solicitantes
- ✅ Solicita con anticipación (mínimo 1 día antes)
- ✅ Verifica que los productos estén disponibles en el catálogo
- ✅ Agrega observaciones si hay urgencia o requisitos especiales
- ❌ No solicites cantidades excesivas innecesariamente

### Para Validadores
- ✅ Revisa la disponibilidad de inventario antes de aprobar
- ✅ Justifica cualquier cambio en las cantidades
- ✅ Rechaza items que no estén disponibles (no dejes cantidades parciales sin justificar)
- ✅ Valida regularmente para evitar acumulación de solicitudes

## Preguntas Frecuentes

### ¿Puedo editar una solicitud después de crearla?
No, una vez creada, la solicitud solo puede ser validada. Si necesitas cambios, cancélala y crea una nueva.

### ¿Qué pasa si se rechaza una solicitud?
La solicitud queda marcada como RECHAZADA. Puedes crear una nueva solicitud con cantidades menores o esperar a que haya disponibilidad.

### ¿Cuánto tiempo tarda en validarse una solicitud?
Depende de la carga de trabajo del equipo de validación. Generalmente se validan dentro de 24 horas.

### ¿Puedo ver el historial de mis solicitudes?
Sí, en la lista de solicitudes puedes filtrar por estado y fecha para ver el historial.

### ¿Qué significa "Cantidad Aprobada"?
Es la cantidad que el validador aprobó. Puede ser igual o menor a la cantidad solicitada.

## Soporte Técnico

Si encuentras problemas:

1. **Error al crear solicitud**: Verifica que hayas completado todos los campos obligatorios
2. **No puedo validar**: Asegúrate de tener permisos de administrador
3. **Productos no aparecen**: Verifica que estén marcados como "Activos" en el catálogo
4. **Otro problema**: Contacta al administrador del sistema

---

**Última actualización**: Diciembre 2024  
**Versión**: 1.0
