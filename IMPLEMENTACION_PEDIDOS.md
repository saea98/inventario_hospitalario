# Implementación de Gestión de Pedidos (Fase 2.2.1)

## Resumen de Cambios

Se ha completado la reconstrucción de la **Fase 2.2.1 (Gestión de Pedidos)** desde cero, eliminando completamente los modelos problemáticos anteriores e implementando una solución nueva y robusta.

## Archivos Creados

### Modelos
- **`inventario/pedidos_models.py`**: Define los nuevos modelos `SolicitudPedido` e `ItemSolicitud`
- **`inventario/migrations/0022_solicitudpedido_itemsolicitud.py`**: Migración para crear las tablas en la base de datos

### Formularios
- **`inventario/pedidos_forms.py`**: Formularios para crear, validar y filtrar solicitudes de pedido

### Vistas
- **`inventario/pedidos_views.py`**: Lógica de negocio para las operaciones de pedidos

### Templates
- **`templates/inventario/pedidos/lista_solicitudes.html`**: Lista de solicitudes con filtros
- **`templates/inventario/pedidos/crear_solicitud.html`**: Formulario para crear nuevas solicitudes
- **`templates/inventario/pedidos/detalle_solicitud.html`**: Detalle de una solicitud específica
- **`templates/inventario/pedidos/validar_solicitud.html`**: Formulario para validar solicitudes

### Configuración
- **`inventario/urls_fase2.py`**: Rutas actualizadas con las nuevas URLs de pedidos

## Archivos Modificados

- **`inventario/models.py`**: Se añadió la importación de los nuevos modelos
- **`inventario/forms.py`**: Se eliminaron los formularios problemáticos de pedidos
- **`templates/base.html`**: Se eliminó el enlace a "Gestión de Pedidos" del menú (se puede restaurar después de las pruebas)

## Pasos para Implementar

### 1. Actualizar el Repositorio Local

```bash
git pull origin main
```

### 2. Reconstruir los Contenedores Docker

```bash
docker compose down -v
docker compose up -d --build
```

### 3. Ejecutar las Migraciones

Una vez que los contenedores estén corriendo, ejecuta:

```bash
docker compose exec web python manage.py migrate
```

### 4. Crear un Superusuario (si es necesario)

```bash
docker compose exec web python manage.py createsuperuser
```

### 5. Acceder a la Aplicación

- **URL de la aplicación**: `http://localhost:8700`
- **Panel de administración**: `http://localhost:8700/admin`

### 6. Probar la Gestión de Pedidos

1. Inicia sesión en la aplicación
2. Navega a **Logística > Gestión de Pedidos**
3. Prueba crear una nueva solicitud
4. Valida la solicitud desde la vista de administrador

## Estructura de Datos

### Modelo SolicitudPedido

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | UUID | Identificador único |
| `folio` | CharField | Folio único de la solicitud (ej: SOL-20231215-ABC123) |
| `institucion_solicitante` | ForeignKey | Institución que solicita |
| `almacen_destino` | ForeignKey | Almacén donde se entregarán los productos |
| `usuario_solicitante` | ForeignKey | Usuario que crea la solicitud |
| `usuario_validacion` | ForeignKey | Usuario que valida la solicitud |
| `fecha_solicitud` | DateTimeField | Fecha de creación |
| `fecha_validacion` | DateTimeField | Fecha de validación |
| `fecha_entrega_programada` | DateField | Fecha programada para la entrega |
| `estado` | CharField | Estado actual (PENDIENTE, VALIDADA, RECHAZADA, etc.) |
| `observaciones_solicitud` | TextField | Observaciones del solicitante |
| `observaciones_validacion` | TextField | Observaciones del validador |

### Modelo ItemSolicitud

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | UUID | Identificador único |
| `solicitud` | ForeignKey | Referencia a la solicitud |
| `producto` | ForeignKey | Producto solicitado |
| `cantidad_solicitada` | PositiveIntegerField | Cantidad solicitada |
| `cantidad_aprobada` | PositiveIntegerField | Cantidad aprobada en validación |
| `justificacion_cambio` | CharField | Justificación si hay cambios |

## Flujo de Uso

1. **Crear Solicitud**: Un usuario crea una nueva solicitud de pedido especificando institución, almacén destino y los items necesarios.

2. **Validar Solicitud**: Un usuario autorizado revisa la solicitud y puede:
   - Aprobar todas las cantidades
   - Modificar cantidades (reducir si no hay disponibilidad)
   - Rechazar items (cantidad aprobada = 0)

3. **Gestionar Estado**: El sistema actualiza automáticamente el estado de la solicitud según las acciones realizadas.

## Notas Importantes

- Los modelos anteriores problemáticos han sido completamente eliminados
- La nueva implementación utiliza UUIDs para mayor seguridad
- Se implementó validación de datos en los formularios
- Se utilizó `@transaction.atomic` en las vistas críticas para garantizar consistencia de datos

## Próximos Pasos (Opcionales)

1. Implementar la generación de órdenes de surtimiento (picking)
2. Agregar la confirmación de salida de existencias
3. Crear reportes de pedidos
4. Implementar notificaciones por correo electrónico
5. Agregar integración con el módulo de Conteo Físico

## Soporte

Si encuentras problemas durante la implementación:

1. Verifica que los contenedores Docker estén corriendo correctamente
2. Revisa los logs: `docker compose logs web`
3. Asegúrate de que la migración se ejecutó correctamente
4. Verifica que el archivo `pedidos_models.py` esté en el directorio correcto

