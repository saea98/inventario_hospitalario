# Pruebas - Sistema de Conteo Físico Progresivo

## Descripción General

El sistema de conteo físico progresivo permite a los usuarios guardar conteos parciales (primer, segundo y tercer conteo) en múltiples sesiones. El MovimientoInventario solo se crea cuando se completa el tercer conteo (definitivo).

## Cambios Implementados

### 1. Modelo `RegistroConteoFisico`
- **Ubicación**: `inventario/models.py` (línea 2026)
- **Campos**:
  - `lote_ubicacion`: OneToOneField a LoteUbicacion
  - `primer_conteo`: PositiveIntegerField (opcional)
  - `segundo_conteo`: PositiveIntegerField (opcional)
  - `tercer_conteo`: PositiveIntegerField (opcional)
  - `observaciones`: TextField
  - `completado`: BooleanField (se marca como True cuando se guarda tercer conteo)
  - `usuario_creacion`: ForeignKey a User
  - `usuario_ultima_actualizacion`: ForeignKey a User
  - `fecha_creacion`, `fecha_actualizacion`: Timestamps

- **Propiedades**:
  - `conteo_definitivo`: Retorna el tercer conteo
  - `progreso`: Retorna "X/3" donde X es cantidad de conteos capturados

### 2. Migración
- **Archivo**: `inventario/migrations/0041_add_registro_conteo_fisico.py`
- **Acción**: Crea tabla `inventario_registroconteofisico`

### 3. Vista `capturar_conteo_lote`
- **Archivo**: `inventario/views_conteo_fisico_v2.py`
- **Cambios**:
  - Obtiene o crea `RegistroConteoFisico` cuando se proporciona `lote_ubicacion_id`
  - Carga datos previos del registro si existen
  - Permite guardar parcialmente (solo algunos conteos)
  - Solo crea `MovimientoInventario` cuando se guarda el tercer conteo
  - Actualiza `LoteUbicacion.cantidad` solo cuando se completa el tercer conteo
  - Sincroniza `Lote.cantidad_disponible` automáticamente

### 4. Template
- **Archivo**: `templates/inventario/conteo_fisico/capturar_conteo.html`
- **Cambios**:
  - Muestra indicador de progreso (X/3) en el header
  - Marca primer conteo como opcional (no requiere asterisco)
  - Carga datos previos en los campos

## Flujo de Prueba

### Escenario 1: Guardado Parcial - Primer Conteo

**Objetivo**: Verificar que se puede guardar solo el primer conteo sin crear MovimientoInventario

**Pasos**:
1. Navegar a "Buscar Lote" en Conteo Físico
2. Buscar un lote específico (ej: por CLAVE o NÚMERO DE LOTE)
3. Seleccionar una ubicación específica
4. En el formulario:
   - Ingresar valor en "Primer Conteo" (ej: 50)
   - Dejar "Segundo Conteo" vacío
   - Dejar "Tercer Conteo" vacío
   - Hacer clic en "Guardar Conteo"

**Resultados Esperados**:
- ✓ Mensaje: "Conteo guardado parcialmente. Progreso: 1/3"
- ✓ Página recarga con los datos guardados
- ✓ Badge en header muestra "Progreso: 1/3"
- ✓ Campo "Primer Conteo" contiene el valor 50
- ✓ NO se crea MovimientoInventario
- ✓ LoteUbicacion.cantidad no cambia

**Validación en BD**:
```sql
SELECT * FROM inventario_registroconteofisico 
WHERE lote_ubicacion_id = <id>;
-- Debe mostrar: primer_conteo=50, segundo_conteo=NULL, tercer_conteo=NULL, completado=false
```

---

### Escenario 2: Regreso y Completar Segundo Conteo

**Objetivo**: Verificar que se cargan datos previos y se puede agregar segundo conteo

**Pasos**:
1. Desde la página anterior (con primer conteo guardado)
2. En el formulario:
   - "Primer Conteo" ya debe estar cargado con 50
   - Ingresar valor en "Segundo Conteo" (ej: 48)
   - Dejar "Tercer Conteo" vacío
   - Hacer clic en "Guardar Conteo"

**Resultados Esperados**:
- ✓ Mensaje: "Conteo guardado parcialmente. Progreso: 2/3"
- ✓ Badge en header muestra "Progreso: 2/3"
- ✓ Ambos campos cargan correctamente (50 y 48)
- ✓ NO se crea MovimientoInventario
- ✓ LoteUbicacion.cantidad no cambia

**Validación en BD**:
```sql
SELECT * FROM inventario_registroconteofisico 
WHERE lote_ubicacion_id = <id>;
-- Debe mostrar: primer_conteo=50, segundo_conteo=48, tercer_conteo=NULL, completado=false
```

---

### Escenario 3: Completar con Tercer Conteo

**Objetivo**: Verificar que se crea MovimientoInventario y se actualiza LoteUbicacion

**Pasos**:
1. Desde la página anterior (con primer y segundo conteo guardados)
2. En el formulario:
   - "Primer Conteo" debe estar cargado con 50
   - "Segundo Conteo" debe estar cargado con 48
   - Ingresar valor en "Tercer Conteo" (ej: 49)
   - Opcionalmente agregar observaciones
   - Hacer clic en "Guardar Conteo"

**Resultados Esperados**:
- ✓ Mensaje: "Conteo completado. Diferencia registrada: +X"
- ✓ Badge en header muestra "Progreso: 3/3"
- ✓ Se crea MovimientoInventario con:
  - `tipo_movimiento`: 'AJUSTE_POSITIVO' o 'AJUSTE_NEGATIVO' según diferencia
  - `cantidad`: valor absoluto de la diferencia
  - `motivo`: Contiene todos los tres conteos y observaciones
- ✓ LoteUbicacion.cantidad se actualiza al valor del tercer conteo (49)
- ✓ Lote.cantidad_disponible se sincroniza

**Validación en BD**:
```sql
-- Verificar registro de conteo completado
SELECT * FROM inventario_registroconteofisico 
WHERE lote_ubicacion_id = <id>;
-- Debe mostrar: primer_conteo=50, segundo_conteo=48, tercer_conteo=49, completado=true

-- Verificar MovimientoInventario creado
SELECT * FROM inventario_movimientoinventario 
WHERE lote_id = <id> 
ORDER BY fecha_creacion DESC LIMIT 1;
-- Debe mostrar tipo_movimiento='AJUSTE_POSITIVO', cantidad=1 (diferencia)

-- Verificar actualización de LoteUbicacion
SELECT cantidad FROM inventario_loteubicacion 
WHERE id = <id>;
-- Debe mostrar: 49
```

---

### Escenario 4: Diferencia Negativa

**Objetivo**: Verificar que se crea AJUSTE_NEGATIVO cuando cantidad contada es menor

**Pasos**:
1. Crear nuevo conteo para otra ubicación
2. Ingresar:
   - Primer Conteo: 100
   - Segundo Conteo: 95
   - Tercer Conteo: 90
3. Guardar

**Resultados Esperados**:
- ✓ Mensaje: "Conteo completado. Diferencia registrada: -10"
- ✓ MovimientoInventario con `tipo_movimiento='AJUSTE_NEGATIVO'`
- ✓ `cantidad=10` (valor absoluto)
- ✓ LoteUbicacion.cantidad = 90

---

### Escenario 5: Sin Diferencia

**Objetivo**: Verificar que se maneja correctamente cuando cantidad contada = cantidad sistema

**Pasos**:
1. Obtener cantidad actual de LoteUbicacion (ej: 75)
2. Ingresar:
   - Primer Conteo: 75
   - Segundo Conteo: 75
   - Tercer Conteo: 75
3. Guardar

**Resultados Esperados**:
- ✓ Mensaje: "Conteo completado. Diferencia registrada: 0"
- ✓ NO se crea MovimientoInventario (diferencia = 0)
- ✓ RegistroConteoFisico.completado = true
- ✓ LoteUbicacion.cantidad permanece en 75

---

## Pruebas de Sincronización

### Prueba 1: Sincronización Lote.cantidad_disponible

**Objetivo**: Verificar que Lote.cantidad_disponible = suma de LoteUbicacion.cantidad

**Pasos**:
1. Completar conteo para una ubicación (cambiar cantidad)
2. Ejecutar en BD:

```sql
SELECT 
    l.id,
    l.cantidad_disponible,
    SUM(lu.cantidad) as suma_ubicaciones
FROM inventario_lote l
LEFT JOIN inventario_loteubicacion lu ON l.id = lu.lote_id
WHERE l.id = <id>
GROUP BY l.id;
```

**Resultado Esperado**:
- ✓ `cantidad_disponible` = `suma_ubicaciones`

---

## Casos de Error

### Error 1: Intento de guardar sin ningún conteo

**Pasos**:
1. Abrir formulario de conteo
2. Dejar todos los campos vacíos
3. Hacer clic en "Guardar Conteo"

**Resultado Esperado**:
- ✓ Mensaje de error: "Debes ingresar al menos un conteo"
- ✓ Formulario no se envía

---

### Error 2: Intento de completar sin tercer conteo (conteo del lote completo)

**Pasos**:
1. Conteo del lote completo (no ubicación específica)
2. Ingresar solo primer y segundo conteo
3. Hacer clic en "Guardar Conteo"

**Resultado Esperado**:
- ✓ Mensaje de error: "El Tercer Conteo (Definitivo) es obligatorio"
- ✓ Formulario no se envía

---

## Checklist de Validación

- [ ] Migración se ejecuta correctamente
- [ ] Modelo RegistroConteoFisico se crea en BD
- [ ] Primer conteo se guarda sin crear MovimientoInventario
- [ ] Segundo conteo se guarda sin crear MovimientoInventario
- [ ] Datos previos se cargan correctamente en el formulario
- [ ] Progreso se muestra correctamente (X/3)
- [ ] Tercer conteo crea MovimientoInventario
- [ ] LoteUbicacion.cantidad se actualiza correctamente
- [ ] Lote.cantidad_disponible se sincroniza
- [ ] Diferencias positivas crean AJUSTE_POSITIVO
- [ ] Diferencias negativas crean AJUSTE_NEGATIVO
- [ ] Sin diferencia no crea MovimientoInventario
- [ ] Observaciones se guardan correctamente
- [ ] Motivo del MovimientoInventario contiene todos los conteos
- [ ] Errores se manejan correctamente
- [ ] Sistema funciona en móvil

---

## Notas Técnicas

### Sincronización de Cantidades

La vista implementa sincronización automática:

```python
# Después de actualizar LoteUbicacion
lote.sincronizar_cantidad_disponible()
```

Este método en el modelo Lote suma todas las cantidades de LoteUbicacion y actualiza cantidad_disponible.

### Creación de MovimientoInventario

Solo se crea cuando:
1. Se guarda el tercer conteo
2. Hay diferencia (cantidad_nueva != cantidad_anterior)

```python
if diferencia != 0:
    MovimientoInventario.objects.create(...)
```

### Motivo Dinámico

El motivo del movimiento se construye dinámicamente incluyendo:
- Todos los conteos capturados
- La diferencia
- Las observaciones (si existen)

---

## Próximos Pasos

1. Ejecutar migración en servidor de desarrollo
2. Ejecutar pruebas manuales siguiendo los escenarios
3. Verificar sincronización en BD
4. Pruebas en dispositivos móviles
5. Documentar cualquier comportamiento inesperado
6. Desplegar a producción

---

## Contacto y Soporte

Para reportar problemas o sugerencias:
- Contactar al equipo de desarrollo
- Incluir logs del servidor
- Proporcionar pasos para reproducir el problema
