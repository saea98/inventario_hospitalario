# Arquitectura Técnica: Gestión de Pedidos (Fase 2.2.1)

## Descripción General

La **Gestión de Pedidos** es un módulo de Django que implementa un sistema completo de solicitud y validación de insumos médicos. Utiliza una arquitectura modular separada en archivos específicos para mejorar la mantenibilidad y escalabilidad.

## Estructura de Archivos

```
inventario/
├── pedidos_models.py          # Modelos de datos
├── pedidos_forms.py           # Formularios
├── pedidos_views.py           # Vistas (lógica de negocio)
├── migrations/
│   └── 0022_solicitudpedido_itemsolicitud.py  # Migración
└── urls_fase2.py              # Rutas (actualizado)

templates/inventario/pedidos/
├── lista_solicitudes.html     # Listado de solicitudes
├── crear_solicitud.html       # Formulario de creación
├── detalle_solicitud.html     # Detalle de solicitud
└── validar_solicitud.html     # Formulario de validación
```

## Modelos de Datos

### SolicitudPedido

**Propósito**: Representa una solicitud completa de insumos médicos.

**Campos Principales**:
```python
id: UUIDField                          # Identificador único
folio: CharField(unique=True)          # Folio generado automáticamente
institucion_solicitante: ForeignKey    # Institución que solicita
almacen_destino: ForeignKey            # Almacén de destino
usuario_solicitante: ForeignKey        # Usuario que crea
usuario_validacion: ForeignKey         # Usuario que valida (nullable)
fecha_solicitud: DateTimeField         # Auto-generada
fecha_validacion: DateTimeField        # Se establece al validar
fecha_entrega_programada: DateField    # Especificada por usuario
estado: CharField(choices)             # Estado actual
observaciones_solicitud: TextField     # Notas del solicitante
observaciones_validacion: TextField    # Notas del validador
```

**Estados Disponibles**:
- `PENDIENTE`: Solicitud creada, esperando validación
- `VALIDADA`: Aprobada con al menos un item
- `RECHAZADA`: Todos los items rechazados
- `EN_PREPARACION`: En proceso de surtimiento
- `PREPARADA`: Lista para entrega
- `ENTREGADA`: Completada
- `CANCELADA`: Cancelada por usuario

**Métodos**:
```python
def save(self, *args, **kwargs)
    # Genera automáticamente el folio si no existe
    # Formato: SOL-YYYYMMDD-XXXXXX
```

### ItemSolicitud

**Propósito**: Representa un producto específico dentro de una solicitud.

**Campos Principales**:
```python
id: UUIDField                          # Identificador único
solicitud: ForeignKey                  # Referencia a SolicitudPedido
producto: ForeignKey                   # Producto solicitado
cantidad_solicitada: PositiveIntegerField  # Cantidad inicial
cantidad_aprobada: PositiveIntegerField    # Cantidad validada (default=0)
justificacion_cambio: CharField        # Razón de cambios (nullable)
```

**Restricciones**:
- Constraint único: `(solicitud, producto)` - No permite duplicados

**Relaciones**:
- Cada ItemSolicitud pertenece a una SolicitudPedido
- Cada ItemSolicitud referencia un Producto
- Al eliminar una SolicitudPedido, se eliminan todos sus items (CASCADE)

## Formularios

### SolicitudPedidoForm
**Uso**: Crear nueva solicitud  
**Campos**: institucion_solicitante, almacen_destino, fecha_entrega_programada, observaciones_solicitud  
**Validaciones**: Fecha mínima = hoy + 1 día

### ItemSolicitudForm
**Uso**: Agregar items a una solicitud  
**Campos**: producto, cantidad_solicitada  
**Validaciones**: Cantidad mínima = 1

### ValidarSolicitudPedidoForm
**Uso**: Validar solicitud (formulario dinámico)  
**Generación**: Se crea dinámicamente con un campo por item  
**Campos por Item**:
- `item_{id}_cantidad_aprobada`: Cantidad a aprobar (0-cantidad_solicitada)
- `item_{id}_justificacion`: Justificación del cambio

### FiltroSolicitudesForm
**Uso**: Filtrar lista de solicitudes  
**Campos**: estado, fecha_inicio, fecha_fin, institucion

### ItemSolicitudFormSet
**Uso**: Editar múltiples items en una solicitud  
**Configuración**: 
- Extra forms: 3
- Permite eliminación: Sí

## Vistas

### lista_solicitudes(request)
**URL**: `/logistica/pedidos/`  
**Método**: GET  
**Permisos**: @login_required  
**Funcionalidad**:
- Obtiene todas las solicitudes con relaciones precargadas
- Aplica filtros si se proporcionan
- Renderiza tabla con paginación

**Contexto**:
```python
{
    'solicitudes': QuerySet,
    'form': FiltroSolicitudesForm,
    'page_title': 'Gestión de Pedidos'
}
```

### crear_solicitud(request)
**URL**: `/logistica/pedidos/crear/`  
**Método**: GET, POST  
**Permisos**: @login_required  
**Decoradores**: @transaction.atomic  
**Funcionalidad**:
- GET: Renderiza formulario vacío con formset
- POST: Valida y guarda solicitud con items
- Establece automáticamente usuario_solicitante

**Validaciones**:
- Formulario principal válido
- Formset válido
- Al menos un item

### detalle_solicitud(request, solicitud_id)
**URL**: `/logistica/pedidos/<uuid:solicitud_id>/`  
**Método**: GET  
**Permisos**: @login_required  
**Funcionalidad**:
- Obtiene solicitud con relaciones precargadas
- Muestra información completa
- Lista todos los items con cantidades

### validar_solicitud(request, solicitud_id)
**URL**: `/logistica/pedidos/<uuid:solicitud_id>/validar/`  
**Método**: GET, POST  
**Permisos**: @login_required  
**Decoradores**: @transaction.atomic  
**Restricciones**: Solo si estado == 'PENDIENTE'  
**Funcionalidad**:
- GET: Renderiza formulario dinámico
- POST: Procesa validación
  - Actualiza cantidad_aprobada para cada item
  - Establece justificación_cambio
  - Calcula nuevo estado basado en aprobaciones
  - Establece usuario_validacion y fecha_validacion

**Lógica de Estado**:
```python
total_aprobado = sum(item.cantidad_aprobada for item in items)
if total_aprobado == 0:
    estado = 'RECHAZADA'
else:
    estado = 'VALIDADA'
```

## Rutas (URLs)

```python
# En inventario/urls_fase2.py, namespace='logistica'

path('pedidos/', pedidos_views.lista_solicitudes, name='lista_solicitudes')
path('pedidos/crear/', pedidos_views.crear_solicitud, name='crear_solicitud')
path('pedidos/<uuid:solicitud_id>/', pedidos_views.detalle_solicitud, name='detalle_solicitud')
path('pedidos/<uuid:solicitud_id>/validar/', pedidos_views.validar_solicitud, name='validar_solicitud')
```

**Uso en templates**:
```html
{% url 'logistica:lista_solicitudes' %}
{% url 'logistica:crear_solicitud' %}
{% url 'logistica:detalle_solicitud' solicitud.id %}
{% url 'logistica:validar_solicitud' solicitud.id %}
```

## Templates

### lista_solicitudes.html
- Tabla responsiva con DataTables
- Filtros en card separada
- Botones de acción (Ver, Validar)
- Badge de estado con colores

### crear_solicitud.html
- Formulario principal para datos de solicitud
- Formset dinámico para items
- Botón "Añadir otro item" con JavaScript
- Validación del lado del cliente

### detalle_solicitud.html
- Información completa de la solicitud
- Tabla de items con cantidades
- Botones de acción contextuales
- Muestra observaciones

### validar_solicitud.html
- Formulario dinámico generado por ValidarSolicitudPedidoForm
- Campo de cantidad aprobada por item
- Campo de justificación por item
- Botones Guardar/Cancelar

## Flujo de Datos

### Crear Solicitud
```
Usuario → Formulario → Vista crear_solicitud() 
    ↓
Validar datos → Guardar SolicitudPedido (usuario_solicitante)
    ↓
Guardar ItemSolicitud para cada item
    ↓
Redirigir a detalle_solicitud()
```

### Validar Solicitud
```
Usuario → Vista validar_solicitud() (GET)
    ↓
Generar ValidarSolicitudPedidoForm dinámico
    ↓
Renderizar formulario
    ↓
Usuario → Enviar validación (POST)
    ↓
Procesar cada item (cantidad_aprobada, justificación)
    ↓
Calcular nuevo estado
    ↓
Guardar cambios (usuario_validacion, fecha_validacion)
    ↓
Redirigir a detalle_solicitud()
```

## Consideraciones de Seguridad

1. **Autenticación**: Todas las vistas requieren @login_required
2. **Autorización**: Se verifica que solo usuarios autenticados accedan
3. **Transacciones**: Operaciones críticas usan @transaction.atomic
4. **Validación**: Todos los formularios validan datos del lado del servidor
5. **CSRF**: Protección CSRF habilitada en formularios

## Rendimiento

### Optimizaciones Implementadas
- `select_related()` para relaciones ForeignKey
- `prefetch_related()` para relaciones inversas
- Índices en campos de búsqueda frecuente

### Consultas Típicas
```python
# Lista con relaciones precargadas
SolicitudPedido.objects.select_related(
    'institucion_solicitante', 'almacen_destino', 
    'usuario_solicitante'
).all()

# Detalle con items
SolicitudPedido.objects.select_related(...).prefetch_related(
    'items__producto'
).get(id=solicitud_id)
```

## Extensiones Futuras

1. **Órdenes de Surtimiento**: Crear modelo para gestionar picking
2. **Salida de Existencias**: Registrar entrega física
3. **Notificaciones**: Email/SMS al validar
4. **Reportes**: Análisis de solicitudes por período
5. **Aprobación en Cascada**: Múltiples niveles de validación
6. **Integración con Inventario**: Reserva automática de stock

## Testing

### Casos de Prueba Recomendados
1. Crear solicitud sin items (debe fallar)
2. Crear solicitud con items duplicados (debe fallar)
3. Validar solicitud con cantidad 0 (debe rechazar)
4. Validar solicitud con cantidades parciales
5. Filtrar por estado y fecha
6. Acceso sin autenticación (debe redirigir)

## Mantenimiento

### Limpieza de Datos
```python
# Eliminar solicitudes antiguas (ej: más de 1 año)
from datetime import timedelta
from django.utils import timezone

cutoff = timezone.now() - timedelta(days=365)
SolicitudPedido.objects.filter(
    estado='ENTREGADA',
    fecha_solicitud__lt=cutoff
).delete()
```

### Monitoreo
- Revisar solicitudes pendientes regularmente
- Alertar si hay solicitudes sin validar > 48 horas
- Monitorear tasa de rechazo

---

**Última actualización**: Diciembre 2024  
**Versión**: 1.0  
**Autor**: Manus AI
