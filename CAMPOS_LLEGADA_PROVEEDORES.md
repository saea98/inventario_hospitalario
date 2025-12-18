# Campos para Llegada de Proveedores (Fase 2.2.2)

## Basado en el Manual de Procesos IMSS-Bienestar y BD ORIGEN CONSOLIDADA

### Flujo de Entrada de Medicamentos

```
1. REGISTRO DE CITAS (Rol: Revisión)
   └─ Cita Programada

2. VALIDACIÓN DE CITA (Rol: Revisión)
   └─ Cita Autorizada

3. RECEPCIÓN FÍSICA (Rol: Almacenero) ← AQUÍ COMIENZAN LOS CAMPOS VERDES
   ├─ Proveedor se presenta
   ├─ Registra datos de remisión
   ├─ Captura medicamentos/insumos
   └─ Estado: En Recepción

4. CONTROL DE CALIDAD (Rol: Control Calidad)
   ├─ Valida productos físicamente
   ├─ Aprueba o rechaza con firma
   ├─ Registra observaciones
   └─ Estado: Aprobado/Rechazado

5. FACTURACIÓN (Rol: Facturación) ← AQUÍ CAPTURA FACTURACIÓN
   ├─ Captura datos de facturación
   ├─ Aplica IVA según tipo de producto
   ├─ Calcula precio unitario con IVA
   ├─ Registra número de procedimiento
   └─ Estado: Facturado

6. SUPERVISIÓN (Rol: Supervisión)
   ├─ Valida captura de datos (Pasos 1, 2, 3)
   ├─ Aprueba o rechaza
   ├─ Firma electrónica
   └─ Estado: Validado/Rechazado

7. ASIGNACIÓN DE UBICACIÓN (Rol: Almacén)
   ├─ Asigna ubicación en almacén
   ├─ Genera etiquetas
   ├─ Bloquea producto hasta tener ubicación
   └─ Estado: Ubicado → Disponible

8. GENERACIÓN DE DOCUMENTO (Sistema)
   ├─ Genera "Entrada de Existencias en Almacén Central"
   ├─ Incluye folio (consecutivo)
   ├─ Adjunta documentos escaneados
   └─ Estado: Documento Generado
```

---

## CAMPOS A CAPTURAR EN LLEGADA DE PROVEEDORES

### Datos de la Cita (Pre-llenados desde Cita Aprobada)

| Campo | Tipo | Obligatorio | Descripción |
|-------|------|------------|------------|
| **Cita ID** | UUID | ✅ | Referencia a la cita programada |
| **Proveedor** | FK | ✅ | Proveedor que llega |
| **RFC del Proveedor** | Texto | ✅ | RFC del proveedor |
| **Fecha Cita Programada** | Fecha | ✅ | Fecha de la cita |
| **Hora Cita Programada** | Hora | ✅ | Hora de la cita |

### Datos de Llegada (CAMPOS VERDES - Captura Almacenero)

| Campo | Tipo | Obligatorio | Descripción |
|-------|------|------------|------------|
| **Fecha Llegada Real** | Fecha | ✅ | Fecha en que el proveedor llega |
| **Hora Llegada Real** | Hora | ✅ | Hora en que el proveedor llega |
| **Remisión** | Texto | ✅ | Número de remisión del proveedor |
| **Número de Piezas Emitidas** | Número | ✅ | Cantidad de piezas según remisión |
| **Número de Piezas Recibidas** | Número | ✅ | Cantidad de piezas físicamente recibidas |
| **Observaciones Recepción** | Texto | ❌ | Observaciones sobre la recepción |

### Datos de Productos (CAMPOS VERDES - Por cada producto)

| Campo | Tipo | Obligatorio | Descripción |
|-------|------|------------|------------|
| **Clave** | Texto | ✅ | Clave del producto (CNIS) |
| **Descripción** | Texto | ✅ | Descripción del producto |
| **Unidad de Medida** | Texto | ✅ | Unidad (piezas, frascos, etc.) |
| **Tipo de Red** | Selección | ✅ | Temperatura Ambiente / Red Fría |
| **Tipo de Insumo** | Selección | ✅ | Medicamento / Material de Curación |
| **Grupo Terapéutico** | Texto | ✅ | Grupo terapéutico del producto |
| **Lote** | Texto | ✅ | Número de lote |
| **Caducidad** | Fecha | ✅ | Fecha de caducidad |
| **Marca** | Texto | ❌ | Marca del producto |
| **Fabricante** | Texto | ❌ | Fabricante del producto |
| **Fecha de Elaboración** | Fecha | ❌ | Fecha de fabricación |

### Datos de Control de Calidad (CAMPOS VERDES - Rol: Control Calidad)

| Campo | Tipo | Obligatorio | Descripción |
|-------|------|------------|------------|
| **Estado Calidad** | Selección | ✅ | Aprobado / Rechazado |
| **Observaciones Calidad** | Texto | ❌ | Observaciones del control de calidad |
| **Firma Control Calidad** | Firma | ✅ | Firma digital del responsable |
| **Fecha Validación Calidad** | Fecha | ✅ | Fecha de validación |
| **Hora Validación Calidad** | Hora | ✅ | Hora de validación |

---

## CAMPOS A CAPTURAR EN FACTURACIÓN (Rol: Facturación)

| Campo | Tipo | Obligatorio | Descripción |
|-------|------|------------|------------|
| **Factura** | Texto | ✅ | Número de factura |
| **Orden de Suministro** | Texto | ✅ | Número de orden de suministro |
| **Contrato** | Texto | ✅ | Número de contrato |
| **Procedimiento** | Texto | ✅ | Número de procedimiento |
| **Programa Presupuestario** | Texto | ✅ | Programa presupuestario |
| **Compra** | Texto | ✅ | Tipo de compra |
| **Precio Unitario sin IVA** | Decimal | ✅ | Precio unitario sin IVA |
| **IVA (%)** | Decimal | ✅ | Porcentaje de IVA según tipo |
| **Precio Unitario con IVA** | Decimal | ✅ | Calculado automáticamente |
| **Subtotal** | Decimal | ✅ | Cantidad × Precio sin IVA |
| **IVA (Importe)** | Decimal | ✅ | Calculado automáticamente |
| **Importe Total** | Decimal | ✅ | Subtotal + IVA |
| **Número de Procedimiento** | Texto | ✅ | Número de procedimiento |
| **Folio** | Texto | ✅ | Folio consecutivo por tipo de entrega |

---

## CAMPOS DE UBICACIÓN EN ALMACÉN (Rol: Almacén)

Estos campos están en el modelo `Lote` y se actualizan en esta fase:

| Campo | Tipo | Obligatorio | Descripción |
|-------|------|------------|------------|
| **Ubicación** | FK | ✅ | Ubicación física en almacén |
| **Almacén** | FK | ✅ | Almacén de destino |
| **Estado** | Selección | ✅ | Ubicado → Disponible |

---

## FLUJO DE ESTADOS

```
LLEGADA DE PROVEEDOR
    ↓
EN_RECEPCION (Almacenero captura datos verdes)
    ↓
CONTROL_CALIDAD (Calidad valida y firma)
    ├─ APROBADO → continúa
    └─ RECHAZADO → fin del proceso
    ↓
FACTURACION (Facturación captura datos)
    ↓
VALIDACION (Supervisión revisa y firma)
    ├─ VALIDADO → continúa
    └─ RECHAZADO → fin del proceso
    ↓
ASIGNACION_UBICACION (Almacén asigna ubicación)
    ↓
UBICADO → DISPONIBLE (Lote disponible para surtimiento)
```

---

## DOCUMENTOS REQUERIDOS

- ✅ Remisión del proveedor
- ✅ Factura
- ✅ Certificado de calidad
- ✅ Otros (según requisitos específicos)

---

## CÁLCULOS AUTOMÁTICOS

### IVA por Tipo de Insumo

- **Medicamentos**: 0% (exento)
- **Material de Curación**: 16%
- **Otros**: 16%

### Precios

```
Precio Unitario con IVA = Precio Unitario sin IVA × (1 + IVA%)
Subtotal = Cantidad × Precio Unitario sin IVA
IVA (Importe) = Subtotal × IVA%
Importe Total = Subtotal + IVA (Importe)
```

---

## CAMPOS DEL MODELO LOTE A ACTUALIZAR

Después de Supervisión Aprobada:

```python
lote.ubicacion = ubicacion_asignada
lote.almacen = almacen_destino
lote.estado = 'DISPONIBLE'
lote.save()
```

---

**Versión**: 1.0  
**Fecha**: Diciembre 2025  
**Basado en**: Manual de Procesos IMSS-Bienestar + BD ORIGEN CONSOLIDADA
