# Manual de Usuario - Fase 2.4: Devoluciones de Proveedores

## 📋 Tabla de Contenidos

1. [Introducción](#introducción)
2. [Conceptos Clave](#conceptos-clave)
3. [Manual de Usuario](#manual-de-usuario)
4. [Documentación Técnica](#documentación-técnica)
5. [Diagramas de Flujo](#diagramas-de-flujo)
6. [Casos de Uso](#casos-de-uso)
7. [Preguntas Frecuentes](#preguntas-frecuentes)

---

## Introducción

### Descripción General

La **Fase 2.4: Devoluciones de Proveedores** es un módulo que permite gestionar el proceso completo de devoluciones de productos a proveedores, incluyendo:

- ✅ Registro de devoluciones
- ✅ Autorización de devoluciones
- ✅ Seguimiento de entregas
- ✅ Generación de notas de crédito
- ✅ Cancelación de devoluciones

### Objetivos

- Mantener un registro detallado de todas las devoluciones
- Facilitar la comunicación con proveedores
- Generar notas de crédito automáticamente
- Rastrear el estado de las devoluciones
- Mejorar la relación con proveedores

### Roles Involucrados

| Rol | Responsabilidades |
|-----|------------------|
| **Encargado de Almacén** | Crear devoluciones, registrar motivos |
| **Supervisor** | Autorizar devoluciones, validar información |
| **Administrador** | Completar devoluciones, generar notas de crédito |
| **Contador** | Registrar notas de crédito en sistema contable |

---

## Conceptos Clave

### Estados de una Devolución

```
PENDIENTE → AUTORIZADA → COMPLETADA
    ↓
 CANCELADA
```

| Estado | Descripción | Acciones Permitidas |
|--------|-------------|-------------------|
| **PENDIENTE** | Devolución creada, esperando autorización | Autorizar, Cancelar |
| **AUTORIZADA** | Devolución aprobada, lista para entregar | Completar, Cancelar |
| **COMPLETADA** | Devolución entregada, nota de crédito generada | Ver detalles |
| **CANCELADA** | Devolución cancelada, no se procesará | Ver detalles |

### Motivos de Devolución

- 🔴 **Producto Defectuoso** - Producto con defectos o daños
- 📅 **Producto Caducado** - Producto vencido o próximo a vencer
- ❌ **Producto Incorrecto** - No corresponde con el pedido
- 📦 **Cantidad Incorrecta** - Cantidad recibida diferente a la solicitada
- 💔 **Embalaje Dañado** - Embalaje deteriorado durante el transporte
- ⚠️ **No Conforme con Especificaciones** - No cumple con estándares de calidad
- 🏥 **Solicitud del Cliente** - Cliente solicita devolución
- 📝 **Otros** - Otros motivos

### Información de Nota de Crédito

La nota de crédito se genera automáticamente cuando se completa una devolución:

- **Número de Nota de Crédito** - Identificador único
- **Fecha de Nota de Crédito** - Fecha de emisión
- **Monto de Nota de Crédito** - Monto total a acreditar (calculado automáticamente)

---

## Manual de Usuario

### 1. Acceso al Módulo

**Ruta:** `/devoluciones/`

**Pasos:**

1. Inicia sesión en el sistema
2. En el menú principal, selecciona **Devoluciones**
3. Se abrirá el dashboard de devoluciones

### 2. Dashboard de Devoluciones

**Ubicación:** `/devoluciones/`

**Funcionalidades:**

- 📊 **Estadísticas Generales**
  - Total de devoluciones
  - Devoluciones pendientes
  - Devoluciones autorizadas
  - Devoluciones completadas
  - Devoluciones canceladas
  - Monto total de devoluciones

- ⚠️ **Alertas**
  - Devoluciones sin entregar hace más de 30 días

- 📋 **Devoluciones Recientes**
  - Últimas 10 devoluciones registradas
  - Estado actual de cada una

- 🏢 **Proveedores con Más Devoluciones**
  - Top 5 proveedores por cantidad de devoluciones

### 3. Lista de Devoluciones

**Ubicación:** `/devoluciones/lista/`

**Funcionalidades:**

#### Búsquedas Separadas

- 🔍 **Buscar por Folio** - Número de devolución (Ej: DEV-20251218-000001)
- 🏢 **Buscar por Proveedor** - Nombre del proveedor
- 📋 **Buscar por Autorización** - Número de autorización

#### Filtros

- **Estado** - Pendiente, Autorizada, Completada, Cancelada
- **Proveedor** - Filtrar por proveedor específico

#### Tabla de Resultados

Muestra:
- Folio de devolución
- Proveedor
- Motivo
- Fecha de creación
- Estado actual
- Cantidad de items
- Monto total
- Número de autorización
- Botones de acción

### 4. Crear Nueva Devolución

**Ubicación:** `/devoluciones/crear/`

**Pasos:**

1. Haz clic en **"Nueva Devolución"**
2. Completa la **Información General**:
   - Selecciona el **Proveedor** *
   - Selecciona el **Motivo General** *
   - Ingresa una **Descripción** (opcional)
   - Datos de **Contacto** (opcional)
   - **Fecha Entrega Estimada** (opcional)

3. Agrega **Items a Devolver**:
   - Haz clic en **"Agregar Item"**
   - Selecciona el **Lote** a devolver
   - Ingresa la **Cantidad**
   - Ingresa el **Precio Unitario**
   - Agrega un **Motivo Específico** (opcional)

4. Revisa el **Resumen**:
   - Total de items
   - Monto total

5. Haz clic en **"Crear Devolución"**

**Validaciones:**
- ✅ Proveedor es obligatorio
- ✅ Motivo general es obligatorio
- ✅ Al menos un item es obligatorio
- ✅ Cantidad debe ser mayor a 0
- ✅ Precio unitario debe ser mayor o igual a 0

### 5. Detalle de Devolución

**Ubicación:** `/devoluciones/<id>/`

**Información Mostrada:**

- **Información General**
  - Folio
  - Proveedor
  - RFC del proveedor
  - Motivo
  - Descripción

- **Contacto**
  - Nombre del contacto
  - Teléfono
  - Email
  - Fecha entrega estimada

- **Items a Devolver**
  - Tabla con todos los items
  - Lote, Producto, Cantidad, Precio, Subtotal

- **Información de Autorización** (si aplica)
  - Número de autorización
  - Fecha de autorización
  - Usuario que autorizó

- **Información de Entrega** (si completada)
  - Fecha de entrega real
  - Número de guía
  - Empresa de transporte
  - Número de nota de crédito
  - Monto de nota de crédito

- **Auditoría**
  - Usuario que creó
  - Fecha de creación
  - Última actualización

**Botones de Acción:**
- ✅ **Autorizar** (si está PENDIENTE)
- ✅ **Completar** (si está AUTORIZADA)
- ❌ **Cancelar** (si no está CANCELADA o COMPLETADA)

### 6. Autorizar Devolución

**Ubicación:** `/devoluciones/<id>/autorizar/`

**Pasos:**

1. Desde el detalle de devolución, haz clic en **"Autorizar"**
2. Ingresa el **Número de Autorización** *
3. Revisa el resumen:
   - Proveedor
   - Total de items
   - Monto total
   - Motivo

4. Haz clic en **"Autorizar Devolución"**

**Resultado:**
- El estado cambia a **AUTORIZADA**
- Se registra la fecha y usuario de autorización
- Se asigna el número de autorización

### 7. Completar Devolución

**Ubicación:** `/devoluciones/<id>/completar/`

**Pasos:**

1. Desde el detalle de devolución, haz clic en **"Completar"**
2. Ingresa la **Fecha de Entrega Real** *
3. Completa la información de entrega (opcional):
   - Número de Guía
   - Empresa de Transporte
   - Número de Nota de Crédito
   - Fecha de Nota de Crédito

4. Revisa el resumen:
   - Proveedor
   - Total de items
   - Monto total
   - Monto de nota de crédito (calculado automáticamente)

5. Haz clic en **"Completar Devolución"**

**Resultado:**
- El estado cambia a **COMPLETADA**
- Se registra la fecha de entrega real
- Se genera la nota de crédito automáticamente
- El monto de la nota de crédito se calcula como el monto total de la devolución

### 8. Cancelar Devolución

**Ubicación:** `/devoluciones/<id>/cancelar/`

**Pasos:**

1. Desde el detalle de devolución, haz clic en **"Cancelar"**
2. Ingresa el **Motivo de Cancelación** *
3. Revisa la información:
   - Folio
   - Proveedor
   - Total de items
   - Monto total
   - Estado actual

4. Haz clic en **"Cancelar Devolución"**

**⚠️ Advertencia:** Esta acción no puede ser revertida

**Resultado:**
- El estado cambia a **CANCELADA**
- Se registra el motivo de cancelación
- La devolución no se procesará

---

## Documentación Técnica

### Arquitectura de Componentes

```
┌─────────────────────────────────────────────────────────┐
│                    Capa de Presentación                 │
│              (Templates HTML + Bootstrap)               │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                   Capa de Aplicación                    │
│         (Vistas, Formularios, Validaciones)             │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                   Capa de Modelos                       │
│    (DevolucionProveedor, ItemDevolucion, Lote)          │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                 Base de Datos                           │
│           (PostgreSQL/MySQL/SQLite)                     │
└─────────────────────────────────────────────────────────┘
```

### Modelos de Datos

#### DevolucionProveedor

```python
class DevolucionProveedor(models.Model):
    # Identificadores
    id (UUID)
    folio (CharField, unique)
    
    # Relaciones
    institucion (ForeignKey)
    proveedor (ForeignKey)
    lotes (ManyToMany through ItemDevolucion)
    
    # Información
    estado (CharField: PENDIENTE, AUTORIZADA, COMPLETADA, CANCELADA)
    motivo_general (CharField)
    descripcion (TextField)
    
    # Contacto
    contacto_proveedor (CharField)
    telefono_proveedor (CharField)
    email_proveedor (EmailField)
    
    # Autorización
    numero_autorizacion (CharField)
    fecha_autorizacion (DateTimeField)
    usuario_autorizo (ForeignKey)
    
    # Entrega
    fecha_entrega_estimada (DateField)
    fecha_entrega_real (DateField)
    numero_guia (CharField)
    empresa_transporte (CharField)
    
    # Nota de Crédito
    numero_nota_credito (CharField)
    fecha_nota_credito (DateField)
    monto_nota_credito (DecimalField)
    
    # Auditoría
    usuario_creacion (ForeignKey)
    fecha_creacion (DateTimeField, auto_now_add)
    fecha_actualizacion (DateTimeField, auto_now)
```

#### ItemDevolucion

```python
class ItemDevolucion(models.Model):
    # Identificadores
    id (UUID)
    devolucion (ForeignKey)
    lote (ForeignKey)
    
    # Información
    cantidad (PositiveIntegerField)
    precio_unitario (DecimalField)
    motivo_especifico (TextField)
    
    # Inspección
    inspeccionado (BooleanField)
    fecha_inspeccion (DateTimeField)
    usuario_inspeccion (ForeignKey)
    observaciones_inspeccion (TextField)
    
    # Auditoría
    fecha_creacion (DateTimeField, auto_now_add)
```

### Vistas Principales

| Vista | Ruta | Método | Descripción |
|-------|------|--------|------------|
| `dashboard_devoluciones` | `/` | GET | Dashboard principal |
| `lista_devoluciones` | `/lista/` | GET | Lista con filtros |
| `crear_devolucion` | `/crear/` | GET, POST | Crear nueva devolución |
| `detalle_devolucion` | `/<id>/` | GET | Ver detalle |
| `autorizar_devolucion` | `/<id>/autorizar/` | GET, POST | Autorizar |
| `completar_devolucion` | `/<id>/completar/` | GET, POST | Completar |
| `cancelar_devolucion` | `/<id>/cancelar/` | GET, POST | Cancelar |

### Formularios

#### DevolucionProveedorForm

Campos:
- `proveedor` - Select2 con proveedores activos
- `motivo_general` - Select con opciones predefinidas
- `descripcion` - Textarea
- `contacto_proveedor` - TextInput
- `telefono_proveedor` - TextInput
- `email_proveedor` - EmailInput
- `fecha_entrega_estimada` - DateInput

#### ItemDevolucionForm

Campos:
- `lote` - Select2 con lotes disponibles
- `cantidad` - NumberInput (mín: 1)
- `precio_unitario` - NumberInput (mín: 0)
- `motivo_especifico` - Textarea

#### ItemDevolucionFormSet

- FormSet inline para múltiples items
- 3 formularios extras por defecto
- Validación de cantidad y precio

### URLs

```
/devoluciones/                          → dashboard_devoluciones
/devoluciones/lista/                    → lista_devoluciones
/devoluciones/crear/                    → crear_devolucion
/devoluciones/<uuid>/                   → detalle_devolucion
/devoluciones/<uuid>/autorizar/         → autorizar_devolucion
/devoluciones/<uuid>/completar/         → completar_devolucion
/devoluciones/<uuid>/cancelar/          → cancelar_devolucion
```

---

## Diagramas de Flujo

### Flujo General de Devolución

```
┌─────────────────────────────────────────────────────────┐
│                   CREAR DEVOLUCIÓN                      │
│  - Seleccionar proveedor                                │
│  - Indicar motivo                                       │
│  - Agregar items                                        │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              DEVOLUCIÓN PENDIENTE                       │
│  - Esperando autorización                               │
│  - Puede ser cancelada                                  │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│            AUTORIZAR DEVOLUCIÓN                         │
│  - Ingresar número de autorización                      │
│  - Registrar fecha y usuario                            │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│            DEVOLUCIÓN AUTORIZADA                        │
│  - Lista para entregar                                  │
│  - Puede ser completada o cancelada                     │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│           COMPLETAR DEVOLUCIÓN                          │
│  - Registrar fecha de entrega                           │
│  - Ingresar información de transporte                   │
│  - Generar nota de crédito                              │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│           DEVOLUCIÓN COMPLETADA                         │
│  - Nota de crédito generada                             │
│  - Proceso finalizado                                   │
└─────────────────────────────────────────────────────────┘
```

### Flujo de Cancelación

```
┌─────────────────────────────────────────────────────────┐
│    DEVOLUCIÓN PENDIENTE O AUTORIZADA                    │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              CANCELAR DEVOLUCIÓN                        │
│  - Ingresar motivo de cancelación                       │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│            DEVOLUCIÓN CANCELADA                         │
│  - No se procesará                                      │
│  - Registro histórico mantenido                         │
└─────────────────────────────────────────────────────────┘
```

---

## Casos de Uso

### Caso 1: Devolución por Producto Defectuoso

**Escenario:** Se recibe un lote de medicamentos defectuosos que debe ser devuelto al proveedor.

**Pasos:**

1. **Crear Devolución**
   - Proveedor: "Farmacéutica XYZ"
   - Motivo: "Producto Defectuoso"
   - Descripción: "Varias unidades presentan grietas en el empaque"
   - Agregar item: Lote 123456, Cantidad 50, Precio $100

2. **Autorizar Devolución**
   - Número de Autorización: "AUTH-001"
   - Estado cambia a AUTORIZADA

3. **Completar Devolución**
   - Fecha de Entrega: 20/12/2025
   - Número de Guía: "GUIA-001"
   - Empresa: "FedEx"
   - Nota de Crédito: NC-001
   - Monto: $5,000

**Resultado:** Devolución completada, nota de crédito generada por $5,000

---

### Caso 2: Devolución por Caducidad

**Escenario:** Se detectan productos caducados en el inventario que deben ser devueltos.

**Pasos:**

1. **Crear Devolución**
   - Proveedor: "Laboratorio ABC"
   - Motivo: "Producto Caducado"
   - Descripción: "Lote caducado el 15/12/2024"
   - Agregar items: Múltiples lotes caducados

2. **Autorizar Devolución**
   - Número de Autorización: "AUTH-002"

3. **Completar Devolución**
   - Registrar información de entrega
   - Generar nota de crédito

**Resultado:** Devolución completada, inventario actualizado

---

### Caso 3: Cancelación de Devolución

**Escenario:** Se cancela una devolución porque el proveedor acepta el producto.

**Pasos:**

1. **Crear Devolución** (PENDIENTE)
2. **Cancelar Devolución**
   - Motivo: "Proveedor aceptó el producto después de inspección"
   - Estado cambia a CANCELADA

**Resultado:** Devolución cancelada, sin procesamiento

---

## Preguntas Frecuentes

### 1. ¿Cuál es la diferencia entre PENDIENTE y AUTORIZADA?

**PENDIENTE:** La devolución ha sido creada pero aún no ha sido autorizada por un supervisor. Está en espera de aprobación.

**AUTORIZADA:** La devolución ha sido aprobada y está lista para ser entregada al proveedor.

---

### 2. ¿Puedo editar una devolución después de crearla?

Actualmente, no es posible editar una devolución después de crearla. Si necesitas cambios, debes cancelarla y crear una nueva.

---

### 3. ¿Qué pasa con la nota de crédito?

La nota de crédito se genera automáticamente cuando completas una devolución. El monto es igual al total de la devolución.

---

### 4. ¿Puedo devolver un lote que ya fue devuelto?

Sí, puedes crear múltiples devoluciones del mismo lote si es necesario. El sistema no restringe esto.

---

### 5. ¿Qué información se necesita para autorizar una devolución?

Solo necesitas ingresar el **Número de Autorización**. Los demás datos (fecha, usuario) se registran automáticamente.

---

### 6. ¿Puedo cancelar una devolución completada?

No, una devolución completada no puede ser cancelada. Solo se pueden cancelar devoluciones en estado PENDIENTE o AUTORIZADA.

---

### 7. ¿Dónde se registra la información de transporte?

La información de transporte (número de guía, empresa) se registra cuando completas la devolución, en el paso final del proceso.

---

### 8. ¿Qué sucede si cancelo una devolución?

La devolución se marca como CANCELADA y no se procesará. Se mantiene el registro histórico para auditoría.

---

### 9. ¿Puedo generar reportes de devoluciones?

Sí, desde el dashboard puedes ver estadísticas y desde la lista puedes filtrar y exportar datos.

---

### 10. ¿Quién puede autorizar una devolución?

Cualquier usuario con acceso al módulo de devoluciones puede autorizar. Se recomienda que sea un supervisor o administrador.

---

### 11. ¿Qué ocurre si ingreso un precio unitario incorrecto?

Puedes cancelar la devolución y crear una nueva con el precio correcto. El sistema recalculará el monto total automáticamente.

---

### 12. ¿Cómo se calcula el monto de la nota de crédito?

Se calcula multiplicando la cantidad de cada item por su precio unitario, sumando todos los items de la devolución.

---

## Resumen de Funcionalidades

| Funcionalidad | Disponible |
|---------------|-----------|
| Crear devoluciones | ✅ |
| Autorizar devoluciones | ✅ |
| Completar devoluciones | ✅ |
| Cancelar devoluciones | ✅ |
| Generar notas de crédito | ✅ |
| Búsqueda por folio | ✅ |
| Búsqueda por proveedor | ✅ |
| Búsqueda por autorización | ✅ |
| Filtro por estado | ✅ |
| Filtro por proveedor | ✅ |
| Dashboard con estadísticas | ✅ |
| Alertas de devoluciones vencidas | ✅ |
| Exportar datos | ✅ |

---

## Checklist de Implementación

- ✅ Modelos de datos creados
- ✅ Vistas implementadas
- ✅ Formularios con validaciones
- ✅ Templates HTML responsivos
- ✅ URLs configuradas
- ✅ Búsquedas separadas
- ✅ Filtros avanzados
- ✅ Dashboard con estadísticas
- ✅ Alertas de devoluciones vencidas
- ✅ Generación automática de notas de crédito
- ✅ Auditoría completa

---

## Soporte y Contacto

Para reportar problemas o sugerencias sobre este módulo, contacta al equipo de desarrollo.

**Versión:** 1.0  
**Fecha:** Diciembre 2025  
**Autor:** Equipo de Desarrollo
