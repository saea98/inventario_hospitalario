# Funcionalidad de Cancelación de Propuestas

## Descripción General

Se ha implementado una funcionalidad completa de cancelación de propuestas de suministro que permite a los usuarios autorizados cancelar propuestas en ciertos estados y liberar automáticamente todas las cantidades reservadas en el inventario.

## Estados Cancelables

Las propuestas pueden ser canceladas únicamente cuando están en los siguientes estados:

- **GENERADA**: Propuesta recién generada, aún no revisada
- **REVISADA**: Propuesta revisada por el almacén, lista para surtimiento
- **EN_SURTIMIENTO**: Propuesta en proceso de surtimiento

## Acciones al Cancelar una Propuesta

Cuando se cancela una propuesta, el sistema realiza automáticamente las siguientes acciones:

### 1. Liberación de Cantidades Reservadas
- Se liberan todas las cantidades que fueron reservadas en los lotes asignados
- Se actualiza el campo `cantidad_reservada` en cada lote
- Las cantidades quedan disponibles para otras propuestas

### 2. Cambio de Estados
- **Propuesta**: Cambia de su estado actual a **CANCELADA**
- **Solicitud**: Vuelve al estado **VALIDADA** para permitir generar una nueva propuesta

### 3. Registro de Auditoría
- Se crea un registro en la tabla `LogPropuesta` con:
  - Usuario que realizó la cancelación
  - Timestamp de la acción
  - Acción: "PROPUESTA CANCELADA"
  - Detalles completos incluyendo:
    - Estado anterior
    - Cantidad total liberada
    - Detalle de cada lote liberado
    - Confirmación de cambios de estado

## Permisos Requeridos

Para cancelar una propuesta, el usuario debe tener uno de los siguientes permisos:

- Ser **superusuario** (`is_superuser=True`)
- Ser **staff** (`is_staff=True`)
- Pertenecer al grupo **"Almacenero"**

## Cómo Usar la Funcionalidad

### Desde la Interfaz Web

1. **Navegar a la propuesta**: Ir a "Logística" → "Propuestas" → Seleccionar una propuesta
2. **Abrir el detalle**: Hacer clic en la propuesta para ver sus detalles
3. **Cancelar**: 
   - Si la propuesta está en estado GENERADA, REVISADA o EN_SURTIMIENTO, aparecerá un botón "Cancelar Propuesta"
   - Hacer clic en el botón rojo "Cancelar Propuesta"
4. **Confirmar**: Se abrirá un modal de confirmación mostrando:
   - Advertencia de que la acción no se puede deshacer
   - Información sobre qué sucederá al cancelar
   - Opción para confirmar o cancelar la operación
5. **Confirmación**: Hacer clic en "Sí, Cancelar Propuesta" para completar la acción

### Desde la API (Programáticamente)

```python
from inventario.propuesta_utils import cancelar_propuesta
from django.contrib.auth.models import User

# Obtener el usuario que realiza la acción
usuario = User.objects.get(username='admin')

# Cancelar la propuesta
resultado = cancelar_propuesta(propuesta_id='uuid-de-la-propuesta', usuario=usuario)

# Verificar el resultado
if resultado['exito']:
    print(f"Éxito: {resultado['mensaje']}")
    print(f"Cantidad liberada: {resultado['cantidad_liberada']} unidades")
else:
    print(f"Error: {resultado['mensaje']}")
```

## Estructura de Datos Retornados

### En Caso de Éxito

```python
{
    'exito': True,
    'mensaje': 'Propuesta SOL-20260115-ABC123 cancelada exitosamente. Se liberaron 150 unidades.',
    'propuesta': <PropuestaPedido object>,
    'cantidad_liberada': 150
}
```

### En Caso de Error

```python
{
    'exito': False,
    'mensaje': 'No se puede cancelar una propuesta en estado Completamente Surtida'
}
```

## Validaciones

El sistema realiza las siguientes validaciones antes de cancelar:

1. **Existencia**: Verifica que la propuesta exista
2. **Estado**: Verifica que la propuesta esté en un estado cancelable
3. **Permisos**: Verifica que el usuario tenga permisos para cancelar
4. **Integridad**: Usa transacciones atómicas para garantizar consistencia

## Archivos Modificados

### 1. `inventario/propuesta_utils.py`
- **Función**: `cancelar_propuesta(propuesta_id, usuario=None)`
- **Cambios**:
  - Mejorado logging con detalles de liberación por lote
  - Cambio de estado a CANCELADA (antes era GENERADA)
  - Retorna cantidad total liberada
  - Mejor manejo de errores

### 2. `inventario/pedidos_views.py`
- **Vista**: `cancelar_propuesta_view(request, propuesta_id)`
- **Cambios**:
  - Validación mejorada de permisos (incluye superusuarios)
  - Validación previa de estado cancelable
  - Mejor manejo de excepciones
  - Cálculo de cantidad total a liberar para mostrar en confirmación
  - Mensajes más informativos al usuario

### 3. `templates/inventario/pedidos/detalle_propuesta.html`
- Ya incluye modal de confirmación
- Botón "Cancelar Propuesta" visible en estados GENERADA, REVISADA, EN_SURTIMIENTO

### 4. `inventario/urls_fase2.py`
- URL ya configurada: `path('propuestas/<uuid:propuesta_id>/cancelar/', pedidos_views.cancelar_propuesta_view, name='cancelar_propuesta')`

### 5. `inventario/pedidos_models.py`
- Modelo `LogPropuesta` para registro de auditoría (ya existía)

## Ejemplo de Flujo Completo

### Escenario: Cancelar una propuesta por cambio de requisitos

1. **Situación inicial**:
   - Propuesta SOL-20260115-ABC123 en estado REVISADA
   - Asignados 100 unidades del Lote L001 y 50 unidades del Lote L002
   - Cantidad reservada en L001: 100, en L002: 50

2. **Usuario cancela la propuesta**:
   - Hace clic en "Cancelar Propuesta"
   - Confirma en el modal

3. **Sistema realiza**:
   - Libera 100 unidades de L001 (cantidad_reservada: 100 → 0)
   - Libera 50 unidades de L002 (cantidad_reservada: 50 → 0)
   - Cambia propuesta a CANCELADA
   - Cambia solicitud a VALIDADA
   - Crea log con detalles de la liberación

4. **Resultado**:
   - Usuario ve mensaje: "Propuesta SOL-20260115-ABC123 cancelada exitosamente. Se liberaron 150 unidades."
   - Se redirige a lista de propuestas
   - Las 150 unidades están disponibles para otras propuestas
   - Se puede generar una nueva propuesta para la misma solicitud

## Consideraciones Importantes

### ✓ Ventajas

- **Reversible**: Se puede generar una nueva propuesta después de cancelar
- **Auditable**: Todos los cambios quedan registrados en LogPropuesta
- **Seguro**: Usa transacciones atómicas para garantizar consistencia
- **Informativo**: Proporciona detalles completos de lo que se libera
- **Flexible**: Permite cancelar en múltiples estados

### ⚠️ Limitaciones

- **No se puede deshacer**: Una vez cancelada, la acción es permanente (pero se puede generar nueva propuesta)
- **Solo ciertos estados**: No se pueden cancelar propuestas en estados SURTIDA, PARCIAL, NO_DISPONIBLE o CANCELADA
- **Permisos requeridos**: Solo usuarios autorizados pueden cancelar

## Testing

Para probar la funcionalidad:

```bash
# 1. Acceder al contenedor
docker exec -it inventario_dev /bin/bash

# 2. Ejecutar las pruebas
python manage.py test inventario.tests.test_cancelacion_propuestas

# 3. O verificar manualmente en la interfaz web
# http://localhost:8700/logistica/propuestas/
```

## Próximos Pasos Sugeridos

1. Crear pruebas unitarias para la función `cancelar_propuesta`
2. Agregar notificaciones por email cuando se cancela una propuesta
3. Permitir cancelación con comentarios adicionales
4. Crear reportes de propuestas canceladas
5. Implementar historial de cambios de estado más detallado

## Soporte

Para reportar problemas o sugerencias sobre esta funcionalidad, contactar al equipo de desarrollo.
