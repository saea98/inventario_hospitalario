# Fase 5 - Movimientos de Suministro de Pedido

## Descripción

Cuando una propuesta de suministro es marcada como **SURTIDA**, el sistema genera automáticamente movimientos de inventario para afectar las existencias y crear trazabilidad completa del flujo.

## Cambios Implementados

### 1. Nueva Función Auxiliar: `generar_movimientos_suministro()`

**Archivo**: `inventario/fase5_utils.py`

```python
def generar_movimientos_suministro(propuesta_id, usuario):
    """
    Genera movimientos de inventario cuando una propuesta se marca como SURTIDA.
    """
```

**Funcionalidad**:
- Itera sobre todos los items de la propuesta
- Para cada lote asignado surtido, crea un movimiento de inventario
- Tipo de movimiento: `SALIDA`
- Actualiza la cantidad disponible del lote
- Registra usuario, fecha y referencia a la propuesta

### 2. Integración en `surtir_propuesta()`

**Archivo**: `inventario/pedidos_views.py`

La función `surtir_propuesta()` ahora:
1. Marca la propuesta como SURTIDA
2. Marca los lotes como surtidos
3. **NUEVO**: Llama a `generar_movimientos_suministro()`
4. Notifica al usuario con el resultado

### 3. Movimientos Generados

Para cada lote surtido se crea un `MovimientoInventario` con:

| Campo | Valor |
|-------|-------|
| **tipo_movimiento** | `SALIDA` |
| **cantidad** | Cantidad surtida del lote |
| **cantidad_anterior** | Cantidad disponible antes |
| **cantidad_nueva** | Cantidad disponible después |
| **motivo** | "Suministro de Pedido - Propuesta {folio}" |
| **documento_referencia** | Folio de la solicitud |
| **pedido** | Folio de la solicitud |
| **folio** | UUID de la propuesta |
| **usuario** | Usuario que surtió |
| **estado** | 1 (Vigente) |

## Flujo Completo

```
1. Usuario accede a propuesta
   ↓
2. Click en "Surtir Propuesta"
   ↓
3. Sistema marca lotes como surtidos
   ↓
4. Propuesta cambia a estado SURTIDA
   ↓
5. ✅ NUEVO: Se generan movimientos de inventario
   ↓
6. Se actualizan cantidades disponibles
   ↓
7. Se crea trazabilidad completa
```

## Ejemplo de Uso

### Antes (Sin Fase 5)
```
Propuesta surtida ✓
Existencias: NO AFECTADAS ✗
Trazabilidad: NO REGISTRADA ✗
```

### Después (Con Fase 5)
```
Propuesta surtida ✓
Existencias: AFECTADAS ✓
Movimientos creados: 5 ✓
Trazabilidad: COMPLETA ✓
```

## Validaciones

- ✅ Verifica que la cantidad disponible sea suficiente
- ✅ Usa transacciones atómicas (todo o nada)
- ✅ Registra errores con mensajes claros
- ✅ Notifica al usuario del resultado

## Mensajes al Usuario

**Éxito**:
```
"Propuesta surtida exitosamente. Se generaron 5 movimientos de inventario"
```

**Advertencia**:
```
"Propuesta surtida pero con advertencia: Error al generar movimientos: ..."
```

## Reportes Disponibles

Los movimientos generados aparecen en:
- **Movimientos de Inventario** → Filtrar por tipo "SALIDA"
- **Reportes** → Análisis de movimientos
- **Trazabilidad** → Por propuesta (folio)

## Beneficios

1. **Trazabilidad Completa**: Cada salida queda registrada
2. **Existencias Actualizadas**: Las cantidades disponibles se afectan automáticamente
3. **Auditoría**: Se registra quién, cuándo y qué se surtió
4. **Consistencia**: Igual que en conteo físico
5. **Reportes**: Análisis de flujos de suministro

## Próximas Mejoras (Opcional)

- Crear tipo de movimiento específico: `SUMINISTRO_PEDIDO`
- Agregar reportes específicos de suministros
- Integrar con devoluciones de áreas
- Análisis de tendencias de suministro
