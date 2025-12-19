# Manual de Gestión de Salidas - Sistema de Inventario Hospitalario

## Tabla de Contenidos

1. [Introducción](#introducción)
2. [Conceptos Básicos](#conceptos-básicos)
3. [Gestión de Salidas](#gestión-de-salidas)
4. [Distribución a Áreas](#distribución-a-áreas)
5. [Reportes y Análisis](#reportes-y-análisis)
6. [Preguntas Frecuentes](#preguntas-frecuentes)

---

## Introducción

La **Fase 4 - Gestión de Salidas** es un módulo integral del Sistema de Inventario Hospitalario que permite registrar, autorizar, distribuir y rastrear la salida de medicamentos y existencias desde los almacenes hacia las diferentes áreas del hospital.

### Objetivos del Módulo

- **Registrar salidas** de existencias de manera organizada y auditable
- **Autorizar salidas** mediante un proceso de validación
- **Distribuir medicamentos** a diferentes áreas hospitalarias
- **Rastrear entregas** y mantener registros de distribuciones
- **Generar reportes** para análisis y toma de decisiones

### Usuarios Autorizados

- **Administrador**: Acceso completo a todas las funciones
- **Gestor de Inventario**: Crear, autorizar y generar reportes
- **Almacenista**: Crear salidas y registrar distribuciones

---

## Conceptos Básicos

### Estados de una Salida

Una salida de existencias puede tener los siguientes estados:

| Estado | Descripción |
|--------|-------------|
| **PENDIENTE** | Salida recién creada, pendiente de autorización |
| **AUTORIZADA** | Salida autorizada y lista para distribuir |
| **COMPLETADA** | Salida completamente distribuida a todas las áreas |
| **CANCELADA** | Salida cancelada con motivo documentado |

### Estados de una Distribución

Una distribución a un área puede tener los siguientes estados:

| Estado | Descripción |
|--------|-------------|
| **PENDIENTE** | Distribución creada, pendiente de envío |
| **EN_TRANSITO** | Distribución en camino hacia el área |
| **ENTREGADA** | Distribución entregada al área |
| **RECHAZADA** | Distribución rechazada por el área |

### Componentes Principales

#### 1. Salida de Existencias (SalidaExistencias)

Cabecera que contiene:
- **Folio**: Identificador único automático (SAL-YYYYMMDD-XXXXXX)
- **Almacén**: Almacén origen de la salida
- **Tipo de Entrega**: Clasificación del tipo de salida
- **Responsable**: Persona responsable de la salida
- **Contacto**: Teléfono y correo del responsable
- **Estado**: Estado actual de la salida
- **Auditoría**: Usuario que creó, fecha de creación, etc.

#### 2. Items de Salida (ItemSalidaExistencias)

Líneas de detalle de una salida:
- **Lote**: Lote de medicamento a salir
- **Cantidad**: Cantidad a salir
- **Precio Unitario**: Precio del lote
- **Subtotal**: Cálculo automático (cantidad × precio)

#### 3. Distribución a Área (DistribucionArea)

Registro de distribución a un área específica:
- **Área Destino**: Nombre del área (Farmacia, Urgencias, etc.)
- **Responsable del Área**: Persona que recibe
- **Contacto**: Teléfono y correo
- **Fecha Estimada**: Fecha prevista de entrega
- **Estado**: Estado de la distribución

#### 4. Items Distribuidos (ItemDistribucion)

Líneas de detalle de una distribución:
- **Item Salida**: Referencia al item de la salida
- **Cantidad Distribuida**: Cantidad enviada a esta área
- **Precio Unitario**: Precio del item
- **Subtotal**: Cálculo automático

---

## Gestión de Salidas

### 1. Crear una Nueva Salida

#### Paso 1: Acceder al Módulo

1. En el menú lateral, selecciona **Gestión Logística**
2. Haz clic en **Gestión de Salidas**
3. Verás la lista de salidas registradas

#### Paso 2: Iniciar Creación

1. Haz clic en el botón **"+ Nueva Salida"** (esquina superior derecha)
2. Se abrirá el formulario de creación

#### Paso 3: Completar Información General

| Campo | Descripción | Requerido |
|-------|-------------|-----------|
| Almacén | Selecciona el almacén origen | Sí |
| Tipo de Entrega | Clasificación de la salida | Sí |
| Fecha Estimada | Fecha prevista de salida | Sí |
| Responsable | Nombre de quien realiza la salida | Sí |
| Teléfono | Contacto del responsable | No |
| Correo | Email del responsable | No |
| Observaciones | Notas adicionales | No |

#### Paso 4: Agregar Items

1. En la sección **"Items de la Salida"**, haz clic en **"+ Agregar Item"**
2. Completa los datos:
   - **Lote**: Selecciona el lote a salir
   - **Cantidad**: Ingresa la cantidad (no puede exceder la disponible)
   - **Precio Unitario**: Se completa automáticamente
   - **Observaciones**: Notas del item (opcional)
3. El **Subtotal** se calcula automáticamente
4. Repite para agregar más items

#### Paso 5: Revisar Resumen

En el panel derecho verás:
- Total de Items
- Monto Total
- Botón para crear la salida

#### Paso 6: Guardar

1. Haz clic en **"Crear Salida"**
2. Se guardará la salida en estado **PENDIENTE**
3. Serás redirigido al detalle de la salida creada

### 2. Autorizar una Salida

#### Requisitos

- La salida debe estar en estado **PENDIENTE**
- Debes tener rol de **Gestor de Inventario** o **Administrador**

#### Proceso

1. Accede al detalle de la salida
2. Haz clic en el botón **"Autorizar"**
3. Ingresa el **Número de Autorización** (único)
4. Haz clic en **"Autorizar Salida"**
5. La salida cambiará a estado **AUTORIZADA**

**Nota**: Una salida autorizada no puede ser modificada, solo cancelada.

### 3. Cancelar una Salida

#### Requisitos

- La salida NO debe estar en estado **COMPLETADA** o **CANCELADA**
- Debes tener rol de **Gestor de Inventario** o **Administrador**

#### Proceso

1. Accede al detalle de la salida
2. Haz clic en el botón **"Cancelar"**
3. Ingresa el **Motivo de Cancelación** (mínimo 10 caracteres)
4. Haz clic en **"Cancelar Salida"**
5. La salida cambiará a estado **CANCELADA**

**Importante**: Esta acción no puede revertirse. Los items volverán al almacén.

### 4. Visualizar Detalles de una Salida

1. En la lista de salidas, haz clic en el icono **"Ver"** o en el folio
2. Se mostrará:
   - Información general de la salida
   - Información de autorización (si está autorizada)
   - Tabla de items incluidos
   - Tabla de distribuciones realizadas
   - Panel con resumen y acciones disponibles

---

## Distribución a Áreas

### 1. Crear una Distribución

#### Requisitos

- La salida debe estar en estado **AUTORIZADA**
- Debe tener al menos un item

#### Proceso

1. Accede al detalle de la salida autorizada
2. Haz clic en el botón **"Distribuir"**
3. Se abrirá el formulario de distribución

#### Paso 1: Información del Área

| Campo | Descripción | Requerido |
|-------|-------------|-----------|
| Área Destino | Nombre del área (Farmacia, Urgencias, etc.) | Sí |
| Responsable del Área | Persona que recibe en el área | Sí |
| Teléfono | Contacto del responsable | No |
| Correo | Email del responsable | No |
| Fecha Estimada | Fecha prevista de entrega | No |

#### Paso 2: Seleccionar Items a Distribuir

1. Haz clic en **"+ Agregar Item a Distribuir"**
2. Selecciona el item de la salida
3. Ingresa la cantidad a distribuir (no puede exceder la disponible)
4. Agrega observaciones si es necesario
5. El subtotal se calcula automáticamente
6. Repite para agregar más items

#### Paso 3: Revisar y Guardar

1. Verifica el resumen en el panel derecho
2. Haz clic en **"Crear Distribución"**
3. La distribución se creará en estado **PENDIENTE**

### 2. Rastrear Distribuciones

En el detalle de la salida, verás una tabla con todas las distribuciones:

| Columna | Información |
|---------|-------------|
| Área Destino | Nombre del área |
| Responsable | Persona que recibe |
| Items | Cantidad de items distribuidos |
| Estado | Estado actual de la distribución |
| Fecha Entrega | Fecha estimada de entrega |

---

## Reportes y Análisis

### 1. Reporte General de Salidas

Acceso: **Gestión Logística → Reportes de Devoluciones → [Nueva opción: Reportes de Salidas]**

#### Características

- **Filtros**: Por fecha, estado y almacén
- **KPIs**: Total de salidas, items, monto total
- **Gráficos**:
  - Salidas por estado (gráfico de pastel)
  - Salidas por almacén (gráfico de barras)
- **Tablas**:
  - Salidas por estado con porcentajes
  - Salidas por almacén con montos
  - Top 10 productos más salidos

#### Interpretación de Datos

- **Salidas Pendientes**: Salidas que aún no han sido autorizadas
- **Salidas Autorizadas**: Salidas listas para distribuir
- **Salidas Completadas**: Salidas completamente distribuidas
- **Salidas Canceladas**: Salidas anuladas

### 2. Análisis de Distribuciones

Acceso: **Gestión Logística → Reportes de Devoluciones → Análisis de Distribuciones**

#### Características

- **Filtros**: Por fecha, estado
- **KPIs**: Total distribuciones, items distribuidos, monto, áreas atendidas
- **Gráficos**:
  - Distribuciones por estado
  - Top 10 áreas que reciben más medicamentos
- **Tablas**:
  - Distribuciones por estado
  - Distribuciones por área

#### Análisis Útil

- Identificar áreas con mayor demanda
- Monitorear entregas rechazadas
- Evaluar eficiencia de distribuciones

### 3. Análisis Temporal

Acceso: **Gestión Logística → Reportes de Devoluciones → Análisis Temporal**

#### Características

- **Período**: Últimos 30 días (personalizable)
- **Gráficos**:
  - Línea temporal de salidas por día
  - Comparación de cantidad vs monto
- **Tablas**:
  - Salidas por día
  - Salidas por semana
  - Estadísticas resumen

#### Análisis Útil

- Identificar patrones de salidas
- Detectar picos de demanda
- Planificar abastecimiento

### 4. Dashboard de Salidas

Acceso: **Gestión Logística → Gestión de Salidas → Dashboard**

#### Información Mostrada

- **KPIs principales**: Total, pendientes, autorizadas, completadas
- **Monto total** de salidas
- **Últimas 10 salidas** registradas
- **Gráficos** de estados y almacenes

---

## Preguntas Frecuentes

### ¿Puedo modificar una salida después de crearla?

**R**: Sí, mientras esté en estado **PENDIENTE**. Una vez autorizada, solo puede cancelarse.

### ¿Qué pasa si cancelo una salida?

**R**: La salida pasa a estado **CANCELADA** y los items vuelven al almacén. Esta acción no puede revertirse.

### ¿Puedo distribuir solo parte de una salida?

**R**: Sí. Puedes crear múltiples distribuciones desde una misma salida, distribuyendo diferentes cantidades a diferentes áreas.

### ¿Qué es el Folio automático?

**R**: Es un identificador único que se genera automáticamente con formato SAL-YYYYMMDD-XXXXXX. Facilita el seguimiento de salidas.

### ¿Puedo ver el historial de cambios de una salida?

**R**: Sí, en el detalle de la salida se muestra quién creó, quién autorizó y cuándo se realizaron estas acciones.

### ¿Cómo se calcula el Subtotal de un item?

**R**: Subtotal = Cantidad × Precio Unitario. Se calcula automáticamente.

### ¿Qué información se requiere para autorizar una salida?

**R**: Solo el **Número de Autorización** (único). Se registra automáticamente quién autoriza y cuándo.

### ¿Puedo generar reportes en Excel?

**R**: Los reportes se pueden visualizar en el navegador. Puedes usar la función de impresión del navegador para guardar como PDF o Excel.

### ¿Qué validaciones se realizan al crear una salida?

**R**: 
- Cantidad solicitada no puede exceder la disponible
- Debe haber al menos un item
- Campos requeridos deben completarse
- No se permiten duplicados de lotes

### ¿Cómo se auditan las salidas?

**R**: Cada salida registra:
- Usuario que creó
- Fecha y hora de creación
- Usuario que autorizó (si aplica)
- Fecha y hora de autorización
- Motivo de cancelación (si aplica)

---

## Soporte y Contacto

Para reportar problemas o sugerencias sobre este módulo, contacta al equipo de soporte del Sistema de Inventario Hospitalario.

---

**Versión**: 1.0  
**Última actualización**: Diciembre 2024  
**Módulo**: Fase 4 - Gestión de Salidas y Distribución
