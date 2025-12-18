# Documentación Técnica - Gestión de Pedidos (Fase 2.2.1)

## Tabla de Contenidos

1. [Arquitectura General](#arquitectura-general)
2. [Modelos de Datos](#modelos-de-datos)
3. [Flujo de Datos](#flujo-de-datos)
4. [Vistas y Lógica de Negocio](#vistas-y-lógica-de-negocio)
5. [Algoritmo de Generación de Propuestas](#algoritmo-de-generación-de-propuestas)
6. [Estructura de Archivos](#estructura-de-archivos)
7. [Migraciones](#migraciones)
8. [Pruebas y Validación](#pruebas-y-validación)

---

## Arquitectura General

### Componentes Principales

```
┌─────────────────────────────────────────────────────────────────┐
│                     GESTIÓN DE PEDIDOS                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐      ┌──────────────────┐                │
│  │   Templates      │      │    Formularios   │                │
│  │  (HTML/CSS)      │      │  (Django Forms)  │                │
│  └────────┬─────────┘      └────────┬─────────┘                │
│           │                         │                           │
│           └─────────────┬───────────┘                           │
│                         │                                       │
│                    ┌────▼─────┐                                │
│                    │   Vistas  │                                │
│                    │ (Views)   │                                │
│                    └────┬──────┘                                │
│                         │                                       │
│        ┌────────────────┼────────────────┐                     │
│        │                │                │                     │
│   ┌────▼────┐    ┌─────▼─────┐    ┌────▼────┐                │
│   │ Modelos  │    │ Generador │    │  Admin  │                │
│   │ (Models) │    │ Propuestas│    │ (ORM)   │                │
│   └────┬─────┘    └─────┬─────┘    └────┬────┘                │
│        │                │                │                     │
│        └────────────────┼────────────────┘                     │
│                         │                                       │
│                    ┌────▼──────────┐                           │
│                    │  Base de Datos │                           │
│                    │  (PostgreSQL)  │                           │
│                    └────────────────┘                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Tecnologías Utilizadas

- **Backend**: Django 4.2.16
- **Base de Datos**: PostgreSQL
- **Frontend**: Bootstrap 5, Select2, jQuery
- **ORM**: Django ORM
- **Validación**: Django Forms

---

## Modelos de Datos

### 1. SolicitudPedido

Representa una solicitud de insumos médicos.

```python
class SolicitudPedido(models.Model):
    ESTADOS = [
        ('PENDIENTE', 'Pendiente de Validación'),
        ('VALIDADA', 'Validada y Aprobada'),
        ('RECHAZADA', 'Rechazada'),
        ('EN_PREPARACION', 'En Preparación'),
        ('PREPARADA', 'Preparada para Entrega'),
        ('ENTREGADA', 'Entregada'),
        ('CANCELADA', 'Cancelada'),
    ]
    
    id = UUIDField(primary_key=True, default=uuid4)
    folio = CharField(max_length=50, unique=True)  # SOL-YYYYMMDD-XXXXXX
    institucion_solicitante = ForeignKey(Institucion, on_delete=CASCADE)
    almacen_destino = ForeignKey(Almacen, on_delete=CASCADE)
    fecha_solicitud = DateTimeField(auto_now_add=True)
    fecha_entrega_programada = DateField()
    estado = CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')
    observaciones_solicitud = TextField(blank=True, null=True)
    usuario_creacion = ForeignKey(User, on_delete=SET_NULL, null=True)
    fecha_creacion = DateTimeField(auto_now_add=True)
    fecha_actualizacion = DateTimeField(auto_now=True)
```

**Campos Clave:**
- `folio`: Identificador único generado automáticamente
- `estado`: Controla el flujo de la solicitud
- `institucion_solicitante`: Institución que solicita
- `almacen_destino`: Almacén donde se entregarán los insumos

---

### 2. ItemSolicitud

Representa cada producto dentro de una solicitud.

```python
class ItemSolicitud(models.Model):
    id = UUIDField(primary_key=True, default=uuid4)
    solicitud = ForeignKey(SolicitudPedido, on_delete=CASCADE, related_name='items')
    producto = ForeignKey(Producto, on_delete=CASCADE)
    cantidad_solicitada = PositiveIntegerField()
    cantidad_aprobada = PositiveIntegerField(default=0)
    justificacion_cambio = TextField(blank=True, null=True)
    fecha_creacion = DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('solicitud', 'producto')
```

**Validaciones:**
- No puede haber duplicados (solicitud + producto)
- `cantidad_aprobada` ≤ `cantidad_solicitada`

---

### 3. PropuestaPedido

Representa la propuesta de surtimiento generada automáticamente.

```python
class PropuestaPedido(models.Model):
    ESTADOS = [
        ('GENERADA', 'Generada'),
        ('REVISADA', 'Revisada'),
        ('SURTIDA', 'Surtida'),
        ('CANCELADA', 'Cancelada'),
    ]
    
    id = UUIDField(primary_key=True, default=uuid4)
    solicitud = ForeignKey(SolicitudPedido, on_delete=CASCADE)
    estado = CharField(max_length=20, choices=ESTADOS, default='GENERADA')
    fecha_generacion = DateTimeField(auto_now_add=True)
    usuario_generacion = ForeignKey(User, on_delete=SET_NULL, null=True, related_name='propuestas_generadas')
    usuario_revision = ForeignKey(User, on_delete=SET_NULL, null=True, blank=True, related_name='propuestas_revisadas')
    usuario_surtimiento = ForeignKey(User, on_delete=SET_NULL, null=True, blank=True, related_name='propuestas_surtidas')
    observaciones = TextField(blank=True, null=True)
```

---

### 4. ItemPropuesta

Representa cada item dentro de una propuesta de surtimiento.

```python
class ItemPropuesta(models.Model):
    id = UUIDField(primary_key=True, default=uuid4)
    propuesta = ForeignKey(PropuestaPedido, on_delete=CASCADE, related_name='items')
    item_solicitud = ForeignKey(ItemSolicitud, on_delete=CASCADE)
    producto = ForeignKey(Producto, on_delete=CASCADE)
    cantidad_propuesta = PositiveIntegerField()
    cantidad_surtida = PositiveIntegerField(default=0)
    observaciones = TextField(blank=True, null=True)
    fecha_creacion = DateTimeField(auto_now_add=True)
```

---

### 5. LoteAsignado

Representa los lotes específicos asignados a cada item de la propuesta.

```python
class LoteAsignado(models.Model):
    id = UUIDField(primary_key=True, default=uuid4)
    item_propuesta = ForeignKey(ItemPropuesta, on_delete=CASCADE, related_name='lotes_asignados')
    lote = ForeignKey(Lote, on_delete=CASCADE)
    cantidad_asignada = PositiveIntegerField()
    observaciones = TextField(blank=True, null=True)
    fecha_creacion = DateTimeField(auto_now_add=True)
```

---

## Flujo de Datos

### 1. Creación de Solicitud

```
Usuario → Formulario → Vista crear_solicitud → 
  ├─ Validar datos
  ├─ Crear SolicitudPedido
  ├─ Crear ItemSolicitud (formset)
  └─ Guardar en BD
```

### 2. Validación de Solicitud

```
Validador → Formulario → Vista validar_solicitud →
  ├─ Validar cantidades
  ├─ Justificar cambios
  ├─ Actualizar ItemSolicitud
  ├─ Cambiar estado a VALIDADA
  └─ Generar PropuestaPedido automáticamente
```

### 3. Generación de Propuesta

```
Sistema (automático) → propuesta_generator.py →
  ├─ Para cada ItemSolicitud:
  │  ├─ Obtener producto
  │  ├─ Buscar lotes disponibles
  │  ├─ Filtrar por caducidad (> 60 días)
  │  ├─ Seleccionar lotes óptimos
  │  └─ Crear ItemPropuesta + LoteAsignado
  └─ Guardar PropuestaPedido
```

### 4. Edición de Propuesta

```
Almacén → Formulario → Vista editar_propuesta →
  ├─ Modificar cantidades
  ├─ Cambiar lotes asignados
  ├─ Actualizar ItemPropuesta + LoteAsignado
  └─ Guardar cambios
```

### 5. Surtimiento

```
Almacén → Confirmar → Vista surtir_propuesta →
  ├─ Para cada LoteAsignado:
  │  ├─ Actualizar Lote.cantidad_disponible
  │  └─ Crear Movimiento (salida)
  ├─ Cambiar estado a SURTIDA
  ├─ Cambiar estado SolicitudPedido a ENTREGADA
  └─ Guardar en BD
```

---

## Vistas y Lógica de Negocio

### Vista: crear_solicitud

**Archivo**: `inventario/pedidos_views.py`

```python
def crear_solicitud(request):
    """
    Crea una nueva solicitud de pedido con items.
    
    GET: Muestra formulario vacío
    POST: Procesa y guarda solicitud + items
    """
    if request.method == 'POST':
        form = SolicitudPedidoForm(request.POST)
        formset = ItemSolicitudFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            # Generar folio único
            folio = generar_folio()
            
            # Crear solicitud
            solicitud = form.save(commit=False)
            solicitud.folio = folio
            solicitud.usuario_creacion = request.user
            solicitud.save()
            
            # Guardar items del formset
            for item_form in formset:
                if item_form.cleaned_data:
                    item = item_form.save(commit=False)
                    item.solicitud = solicitud
                    item.save()
            
            return redirect('logistica:detalle_pedido', pk=solicitud.pk)
```

### Vista: validar_solicitud

**Archivo**: `inventario/pedidos_views.py`

```python
def validar_solicitud(request, pk):
    """
    Valida una solicitud y genera propuesta automáticamente.
    """
    solicitud = get_object_or_404(SolicitudPedido, pk=pk)
    
    if request.method == 'POST':
        form = ValidarSolicitudPedidoForm(request.POST, instance=solicitud)
        
        if form.is_valid():
            # Actualizar cantidades aprobadas
            for item in solicitud.items.all():
                cantidad_aprobada = request.POST.get(f'cantidad_aprobada_{item.id}')
                justificacion = request.POST.get(f'justificacion_{item.id}')
                
                item.cantidad_aprobada = int(cantidad_aprobada) if cantidad_aprobada else 0
                item.justificacion_cambio = justificacion
                item.save()
            
            # Cambiar estado
            solicitud.estado = 'VALIDADA'
            solicitud.save()
            
            # Generar propuesta automáticamente
            try:
                propuesta = generar_propuesta_pedido(solicitud)
                messages.success(request, 'Solicitud validada. Propuesta generada.')
            except Exception as e:
                messages.error(request, f'Error al generar propuesta: {str(e)}')
            
            return redirect('logistica:lista_pedidos')
```

### Función: generar_propuesta_pedido

**Archivo**: `inventario/propuesta_generator.py`

Esta es la función más crítica del sistema. Genera automáticamente la propuesta basada en reglas.

```python
def generar_propuesta_pedido(solicitud):
    """
    Genera una propuesta de surtimiento basada en:
    1. Disponibilidad en inventario
    2. Validación de caducidad (> 60 días)
    3. Optimización de cantidades
    4. Sugerencias de alternativas
    """
    propuesta = PropuestaPedido.objects.create(
        solicitud=solicitud,
        estado='GENERADA'
    )
    
    for item_solicitud in solicitud.items.all():
        if item_solicitud.cantidad_aprobada == 0:
            continue
        
        # Crear item de propuesta
        item_propuesta = ItemPropuesta.objects.create(
            propuesta=propuesta,
            item_solicitud=item_solicitud,
            producto=item_solicitud.producto,
            cantidad_propuesta=item_solicitud.cantidad_aprobada
        )
        
        # Buscar lotes disponibles
        lotes_disponibles = obtener_lotes_validos(
            producto=item_solicitud.producto,
            almacen=solicitud.almacen_destino,
            cantidad_requerida=item_solicitud.cantidad_aprobada
        )
        
        # Asignar lotes
        cantidad_pendiente = item_solicitud.cantidad_aprobada
        for lote in lotes_disponibles:
            if cantidad_pendiente <= 0:
                break
            
            cantidad_a_asignar = min(
                cantidad_pendiente,
                lote.cantidad_disponible
            )
            
            LoteAsignado.objects.create(
                item_propuesta=item_propuesta,
                lote=lote,
                cantidad_asignada=cantidad_a_asignar
            )
            
            cantidad_pendiente -= cantidad_a_asignar
    
    return propuesta


def obtener_lotes_validos(producto, almacen, cantidad_requerida):
    """
    Obtiene lotes válidos para surtimiento.
    
    Criterios:
    1. Producto coincide
    2. Almacén coincide
    3. Cantidad disponible > 0
    4. Estado = DISPONIBLE
    5. Días para caducar > 60
    """
    hoy = date.today()
    fecha_minima_caducidad = hoy + timedelta(days=60)
    
    lotes = Lote.objects.filter(
        producto=producto,
        almacen=almacen,
        cantidad_disponible__gt=0,
        estado='DISPONIBLE',
        fecha_caducidad__gt=fecha_minima_caducidad
    ).order_by('fecha_caducidad')  # FIFO: primero los que vencen antes
    
    return lotes
```

---

## Algoritmo de Generación de Propuestas

### Pseudocódigo

```
FUNCIÓN generar_propuesta(solicitud):
    CREAR propuesta_pedido
    
    PARA CADA item_solicitud EN solicitud.items:
        SI item_solicitud.cantidad_aprobada > 0:
            CREAR item_propuesta
            
            lotes ← obtener_lotes_validos(
                producto=item_solicitud.producto,
                almacen=solicitud.almacen_destino,
                caducidad_minima=HOY + 60_DIAS
            )
            
            cantidad_pendiente ← item_solicitud.cantidad_aprobada
            
            PARA CADA lote EN lotes:
                SI cantidad_pendiente > 0:
                    cantidad_asignar ← MIN(
                        cantidad_pendiente,
                        lote.cantidad_disponible
                    )
                    
                    CREAR lote_asignado(
                        item_propuesta=item_propuesta,
                        lote=lote,
                        cantidad=cantidad_asignar
                    )
                    
                    cantidad_pendiente ← cantidad_pendiente - cantidad_asignar
    
    RETORNAR propuesta_pedido
FIN FUNCIÓN
```

### Validaciones Clave

1. **Caducidad**: Solo lotes con > 60 días de vigencia
2. **Disponibilidad**: Solo lotes con cantidad_disponible > 0
3. **Estado**: Solo lotes en estado DISPONIBLE
4. **Cantidad**: No se asigna más de lo disponible

---

## Estructura de Archivos

```
inventario_hospitalario/
├── inventario/
│   ├── pedidos_models.py          # Modelos SolicitudPedido, ItemSolicitud, etc.
│   ├── pedidos_forms.py           # Formularios para solicitudes y propuestas
│   ├── pedidos_views.py           # Vistas para gestión de pedidos
│   ├── propuesta_generator.py     # Lógica de generación de propuestas
│   ├── urls_fase2.py              # URLs de la Fase 2
│   └── migrations/
│       └── 0022_cleanup_and_create_pedidos.py
│       └── 0023_itempropuesta_loteasignado_propuestapedido_and_more.py
│
├── templates/inventario/pedidos/
│   ├── lista_solicitudes.html     # Lista de solicitudes
│   ├── crear_solicitud.html       # Formulario de creación
│   ├── detalle_solicitud.html     # Detalle de solicitud
│   ├── validar_solicitud.html     # Formulario de validación
│   ├── lista_propuestas.html      # Lista de propuestas
│   ├── detalle_propuesta.html     # Detalle de propuesta
│   ├── editar_propuesta.html      # Edición de propuesta
│   └── revisar_propuesta.html     # Revisión de propuesta
│
└── DOCUMENTACION_TECNICA_GESTION_PEDIDOS.md
```

---

## Migraciones

### Migración 0022: Limpieza y Creación de Modelos

```python
# Elimina tablas duplicadas si existen
# Crea nuevas tablas con estructura correcta
```

### Migración 0023: Propuestas de Surtimiento

```python
# Crea tablas:
# - inventario_itempropuesta
# - inventario_loteasignado
# - inventario_propuestapedido
```

---

## Pruebas y Validación

### Casos de Prueba

#### 1. Crear Solicitud Válida

```
Entrada:
- Institución: Centro de Salud A
- Almacén: Vallejo
- Items: Producto X (cantidad 100)

Resultado Esperado:
- Solicitud creada con estado PENDIENTE
- Folio generado correctamente
- Items guardados
```

#### 2. Validar Solicitud

```
Entrada:
- Solicitud con 3 items
- Validador aprueba 2 items, rechaza 1

Resultado Esperado:
- Solicitud estado VALIDADA
- Propuesta generada automáticamente
- Items con cantidades correctas
```

#### 3. Generar Propuesta

```
Entrada:
- Solicitud validada con cantidad_aprobada=100

Resultado Esperado:
- Propuesta creada
- Lotes asignados correctamente
- Solo lotes con caducidad > 60 días
- Cantidad total asignada = 100
```

#### 4. Editar Propuesta

```
Entrada:
- Propuesta generada
- Cambiar cantidad de 100 a 80

Resultado Esperado:
- ItemPropuesta actualizado
- LoteAsignado recalculado
- Cambios guardados
```

#### 5. Surtir Propuesta

```
Entrada:
- Propuesta revisada
- Confirmar surtimiento

Resultado Esperado:
- Inventario actualizado
- Movimientos registrados
- Solicitud estado ENTREGADA
- Propuesta estado SURTIDA
```

### Validaciones de Negocio

1. **No puede haber dos items iguales en una solicitud**
   ```python
   unique_together = ('solicitud', 'producto')
   ```

2. **Cantidad aprobada no puede ser mayor a solicitada**
   ```python
   if cantidad_aprobada > cantidad_solicitada:
       raise ValidationError()
   ```

3. **Solo se pueden surtir lotes con caducidad > 60 días**
   ```python
   fecha_minima = today + timedelta(days=60)
   lotes = Lote.objects.filter(fecha_caducidad__gt=fecha_minima)
   ```

4. **La cantidad total asignada debe coincidir con la aprobada**
   ```python
   total_asignado = sum(lote.cantidad_asignada for lote in lotes_asignados)
   assert total_asignado == item_propuesta.cantidad_propuesta
   ```

---

## Seguridad y Permisos

### Permisos Requeridos

- **Crear Solicitud**: `inventario.add_solicitudpedido`
- **Validar Solicitud**: `inventario.change_solicitudpedido`
- **Editar Propuesta**: `inventario.change_propuestapedido`
- **Surtir Propuesta**: `inventario.delete_lote` (actualiza inventario)

### Validaciones de Seguridad

1. **Usuario autenticado**: Todas las vistas requieren login
2. **Permisos verificados**: Decoradores `@login_required`
3. **Datos validados**: Formularios Django con validación
4. **Transacciones atómicas**: Operaciones críticas en transacciones

---

## Optimizaciones y Consideraciones

### Base de Datos

- Índices en campos frecuentemente consultados:
  - `SolicitudPedido.estado`
  - `SolicitudPedido.fecha_solicitud`
  - `Lote.fecha_caducidad`
  - `Lote.cantidad_disponible`

### Rendimiento

- Uso de `select_related()` para evitar N+1 queries
- Uso de `prefetch_related()` para relaciones muchos-a-muchos
- Paginación en listas

### Escalabilidad

- Modelos diseñados para manejar millones de registros
- UUIDs para evitar colisiones
- Índices apropiados en BD

---

## Troubleshooting

### Error: "relation 'inventario_solicitudpedido' already exists"

**Causa**: Migraciones duplicadas  
**Solución**: Ejecutar `python manage.py migrate --fake 0022`

### Error: "Cannot resolve keyword 'existencia_actual'"

**Causa**: Nombre de campo incorrecto  
**Solución**: Usar `cantidad_disponible` en lugar de `existencia_actual`

### Propuesta no se genera automáticamente

**Causa**: Validación no cambió estado a VALIDADA  
**Solución**: Verificar que `solicitud.estado = 'VALIDADA'` se ejecute

### Lotes no aparecen en propuesta

**Causa**: Lotes con caducidad < 60 días  
**Solución**: Verificar `fecha_caducidad` de los lotes

---

## Contacto y Soporte Técnico

Para problemas técnicos, contactar al equipo de desarrollo:
- **Email**: desarrollo@imss-bienestar.gob.mx
- **GitHub**: [Repositorio del proyecto]
- **Documentación**: [URL de documentación]

---

**Versión**: 1.0  
**Última actualización**: Diciembre 2025  
**Desarrollado por**: Equipo de Inventario Hospitalario IMSS-Bienestar
