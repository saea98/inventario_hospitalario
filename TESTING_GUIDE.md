# Guía de Testing - Fase 2.2.2 Llegada de Proveedores

## Escenarios de Prueba

### Escenario 1: Crear Llegada Básica

**Objetivo**: Validar que se puede crear una llegada con los nuevos campos

**Pasos**:
1. Navegar a `/logistica/llegadas/crear/`
2. Seleccionar una cita autorizada
3. Llenar datos:
   - Remisión: `REM-001`
   - Piezas Emitidas: `100`
   - Piezas Recibidas: `100`
   - Almacén: Seleccionar uno disponible
   - Tipo de Red: Seleccionar "Red Fría" o "Red Seca"
4. Agregar un item:
   - Producto: Seleccionar uno
   - Lote: `LOTE-001`
   - Caducidad: Fecha válida
   - Cant. Emitida: `50`
   - Cant. Recibida: `50`
   - Piezas/Lote: `50`
   - Marca: `Marca X`
5. Hacer clic en "Guardar Llegada"

**Resultado Esperado**:
- ✓ Llegada creada exitosamente
- ✓ Folio generado automáticamente
- ✓ Almacén guardado correctamente
- ✓ Tipo de red guardado
- ✓ Item creado con piezas_por_lote = 50

---

### Escenario 2: Validación de Piezas por Lote

**Objetivo**: Validar que la suma de piezas_por_lote debe ser igual a cantidad_recibida

**Pasos**:
1. Crear llegada con múltiples items del mismo producto
2. Item 1:
   - Cant. Recibida: `100`
   - Piezas/Lote: `50`
3. Item 2 (agregar fila):
   - Cant. Recibida: `50`
   - Piezas/Lote: `30` (INCORRECTO - debería ser 50)
4. Intentar guardar

**Resultado Esperado**:
- ✓ JavaScript muestra validación en tiempo real
- ✓ Campo piezas_por_lote se resalta en rojo
- ✓ Mensaje de error: "La suma de piezas por lote debe ser igual a la cantidad recibida"
- ✓ Formulario NO se envía

---

### Escenario 3: Validación Correcta de Piezas

**Objetivo**: Validar que la suma correcta de piezas permite guardar

**Pasos**:
1. Crear llegada con múltiples items
2. Item 1:
   - Cant. Recibida: `100`
   - Piezas/Lote: `100`
3. Item 2:
   - Cant. Recibida: `50`
   - Piezas/Lote: `50`
4. Guardar

**Resultado Esperado**:
- ✓ Validación pasa
- ✓ Llegada se guarda exitosamente
- ✓ Ambos items se crean correctamente

---

### Escenario 4: Cálculo Automático de IVA

**Objetivo**: Validar que el IVA se calcula automáticamente según la clave

**Pasos**:
1. Crear llegada y llegar a fase de facturación
2. Item con clave 060001:
   - Precio unitario: `100.00`
   - IVA debe calcularse automáticamente como 16%
3. Item con clave 010001:
   - Precio unitario: `100.00`
   - IVA debe calcularse automáticamente como 0%

**Resultado Esperado**:
- ✓ Item 1: IVA = 16%, Precio con IVA = 116.00
- ✓ Item 2: IVA = 0%, Precio con IVA = 100.00
- ✓ Cálculos automáticos sin intervención del usuario

---

### Escenario 5: Cambio de Almacén

**Objetivo**: Validar que el almacén es editable

**Pasos**:
1. Crear llegada con Almacén A
2. Guardar
3. Editar llegada
4. Cambiar a Almacén B
5. Guardar

**Resultado Esperado**:
- ✓ Almacén se puede cambiar
- ✓ Cambio se guarda correctamente
- ✓ No hay restricciones de edición

---

### Escenario 6: Validación de Cantidad Recibida

**Objetivo**: Validar que cantidad_recibida no puede ser mayor a cantidad_emitida

**Pasos**:
1. Crear llegada con item:
   - Cant. Emitida: `50`
   - Cant. Recibida: `100` (INCORRECTO)
2. Cambiar cantidad_recibida

**Resultado Esperado**:
- ✓ Campo se resalta en rojo
- ✓ Mensaje: "No puede ser mayor a cantidad emitida"
- ✓ Validación en tiempo real

---

### Escenario 7: Agregar y Eliminar Filas

**Objetivo**: Validar que se pueden agregar y eliminar items dinámicamente

**Pasos**:
1. Crear llegada
2. Hacer clic en "+ Agregar Fila" 3 veces
3. Llenar datos en cada fila
4. Eliminar la fila 2
5. Guardar

**Resultado Esperado**:
- ✓ Se agregan filas correctamente
- ✓ Select2 funciona en nuevas filas
- ✓ Se pueden eliminar filas
- ✓ Solo se guardan filas no eliminadas

---

### Escenario 8: Validación de Campos Requeridos

**Objetivo**: Validar que los campos requeridos son obligatorios

**Pasos**:
1. Intentar crear llegada sin llenar:
   - Cita Autorizada
   - Remisión
   - Almacén
2. Intentar guardar

**Resultado Esperado**:
- ✓ Errores de validación mostrados
- ✓ Campos resaltados en rojo
- ✓ Formulario no se envía

---

### Escenario 9: Integración con Cita Autorizada

**Objetivo**: Validar que la llegada se vincula correctamente con la cita

**Pasos**:
1. Crear cita autorizada
2. Crear llegada desde esa cita
3. Verificar que los datos se heredan

**Resultado Esperado**:
- ✓ Proveedor se hereda de la cita
- ✓ Almacén de la cita se pre-llena (si aplica)
- ✓ Folio se genera correctamente

---

### Escenario 10: Múltiples Lotes del Mismo Producto

**Objetivo**: Validar que se pueden registrar múltiples lotes del mismo producto

**Pasos**:
1. Crear llegada con 2 items del mismo producto pero diferente lote:
   - Item 1: Lote A, Cant. 50, Piezas 50
   - Item 2: Lote B, Cant. 50, Piezas 50
2. Guardar

**Resultado Esperado**:
- ✓ Ambos items se guardan
- ✓ No hay conflicto de unicidad
- ✓ Se pueden diferenciar por lote

---

## Casos de Prueba por Ambiente

### DEV (Desarrollo)

```
Pruebas a ejecutar:
- Escenarios 1-10 (todos)
- Pruebas de rendimiento
- Pruebas de carga
- Validación de logs
```

### QA (Calidad)

```
Pruebas a ejecutar:
- Escenarios 1-10 (todos)
- Pruebas de integración
- Pruebas de seguridad
- Pruebas de compatibilidad de navegadores
```

### PROD (Productivo)

```
Pruebas a ejecutar:
- Escenarios 1, 3, 5, 9 (críticos)
- Monitoreo de errores
- Validación de performance
- Verificación de backups
```

---

## Matriz de Compatibilidad

| Navegador | Versión | Estado |
|-----------|---------|--------|
| Chrome | 120+ | ✓ Soportado |
| Firefox | 121+ | ✓ Soportado |
| Safari | 17+ | ✓ Soportado |
| Edge | 120+ | ✓ Soportado |
| IE 11 | - | ✗ No soportado |

---

## Criterios de Aceptación

### Funcionalidad
- [ ] Todos los campos nuevos se muestran correctamente
- [ ] Validaciones funcionan en tiempo real
- [ ] Cálculos de IVA son automáticos
- [ ] Piezas por lote se valida correctamente

### Rendimiento
- [ ] Carga de formulario < 2 segundos
- [ ] Guardado de llegada < 3 segundos
- [ ] Sin errores de JavaScript en consola

### Seguridad
- [ ] CSRF token presente
- [ ] Validación en servidor
- [ ] Permisos verificados

### Usabilidad
- [ ] Interfaz intuitiva
- [ ] Mensajes de error claros
- [ ] Flujo lógico

---

## Reporte de Testing

### Plantilla

```
Ambiente: [DEV/QA/PROD]
Fecha: YYYY-MM-DD
Tester: Nombre

Escenario 1: [PASÓ/FALLÓ]
- Detalles:
- Errores encontrados:

Escenario 2: [PASÓ/FALLÓ]
- Detalles:
- Errores encontrados:

...

Resumen:
- Total Escenarios: 10
- Pasados: X
- Fallidos: Y
- Bloqueantes: Z

Observaciones:
```

---

## Checklist Pre-Despliegue

- [ ] Código revisado en GitHub
- [ ] Migraciones creadas y probadas
- [ ] Formularios actualizados
- [ ] Templates actualizados
- [ ] JavaScript validado
- [ ] Todos los escenarios probados en DEV
- [ ] Documentación actualizada
- [ ] Backup de BD creado
- [ ] Equipo notificado
- [ ] Plan de rollback preparado

---

**Versión**: 1.0  
**Fecha**: 2025-01-17  
**Próxima Revisión**: 2025-02-17
