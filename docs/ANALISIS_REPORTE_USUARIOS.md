# Análisis: Reporte de Usuarios del Sistema y Resumen de Actividades

## 1. Tabla LogSistema (`inventario_logsistema`)

La tabla **LogSistema** ya existe en el proyecto y se usa para:

- **Registro de errores**: el middleware registra excepciones no manejadas (nivel ERROR, tipo SISTEMA) con `usuario`, `url`, `ip_cliente`, `fecha_creacion`.
- **Campos útiles para el reporte**: `usuario_id`, `nivel`, `tipo`, `titulo`, `fecha_creacion`.

**Conclusión**: Podemos usar LogSistema para contar, por usuario, cuántos eventos/errores se registraron (por ejemplo, entradas en logs en un periodo). No requiere migraciones.

---

## 2. Actividades por usuario (sin migraciones)

Todas las secciones del sistema que tienen relación con usuario ya cuentan con `usuario_id` (o FK a User). A continuación, los modelos y el **related_name** que permite contar actividades por usuario.

| Actividad | Modelo | Campo / related_name | Descripción |
|-----------|--------|----------------------|-------------|
| Pedidos solicitados | SolicitudPedido (pedidos_models) | usuario_solicitante → `pedidos_solicitados` | Solicitudes de pedido creadas por el usuario |
| Pedidos validados | SolicitudPedido | usuario_validacion → `pedidos_validados` | Solicitudes validadas por el usuario |
| Propuestas generadas | PropuestaPedido (pedidos_models) | usuario_generacion → `propuestas_generadas` | Propuestas de suministro generadas |
| Propuestas revisadas | PropuestaPedido | usuario_revision → `propuestas_revisadas` | Propuestas revisadas por almacén |
| Propuestas surtidas | PropuestaPedido | usuario_surtimiento → `propuestas_surtidas` | Propuestas surtidas (confirmación final) |
| Ítems recogidos (picking) | LoteAsignado (pedidos_models) | usuario_surtido → `lotes_asignados_surtidos` | Ítems marcados como recogidos en picking electrónico |
| Citas creadas | CitaProveedor (models) | usuario_creacion → `citas_creadas` | Citas de proveedor creadas |
| Citas autorizadas | CitaProveedor | usuario_autorizacion → `citas_autorizadas` | Citas autorizadas |
| Citas canceladas | CitaProveedor | usuario_cancelacion → `citas_canceladas` | Citas canceladas |
| Conteos creados | ConteoFisico (models) | usuario_creacion → `conteos_creados` | Conteos físicos creados |
| Traslados creados | OrdenTraslado (models) | usuario_creacion → `traslados_creados` | Órdenes de traslado creadas |
| Llegadas creadas | LlegadaProveedor (llegada_models) | creado_por → `llegadas_creadas` | Llegadas de proveedor (recepción) |
| Llegadas calidad | LlegadaProveedor | usuario_calidad → `llegadas_validadas_calidad` | Validación de calidad |
| Llegadas facturación | LlegadaProveedor | usuario_facturacion → `llegadas_facturadas` | Facturación en llegada |
| Llegadas supervisadas | LlegadaProveedor | usuario_supervision → `llegadas_supervisadas` | Supervisión de llegada |
| Llegadas ubicadas | LlegadaProveedor | usuario_ubicacion → `llegadas_ubicadas` | Asignación de ubicación |
| Devoluciones creadas | DevolucionProveedor (models) | usuario_creacion → `devoluciones_creadas` | Devoluciones a proveedor creadas |
| Devoluciones autorizadas | DevolucionProveedor | usuario_autorizo → `devoluciones_autorizadas` | Devoluciones autorizadas |
| Items devolución inspeccionados | ItemDevolucion (models) | usuario_inspeccion → `items_devolucion_inspeccionados` | Items de devolución inspeccionados |
| Salidas autorizadas | SalidaExistencias (models) | usuario_autoriza → `salidas_autorizadas` | Salidas de existencias autorizadas |
| Distribuciones creadas | DistribucionArea (models) | usuario_creacion → `distribuciones_creadas` | Distribuciones a área creadas |
| Listas de revisión creadas | ListaRevision (models) | usuario_creacion → `listas_revision_creadas` | Listas de revisión creadas |
| Listas de revisión validadas | ListaRevision | usuario_validacion → `listas_revision_validadas` | Listas validadas |
| Registros conteo creados | RegistroConteoFisico (models) | usuario_creacion → `registros_conteo_creados` | Registros de conteo físico |
| Movimientos creados | MovimientoInventario (models) | usuario → `movimientoinventario_set` | Movimientos de inventario (creación) |
| Movimientos anulados | MovimientoInventario | usuario_anulacion → `movimientos_anulados` | Movimientos anulados por el usuario |
| Logs de sistema | LogSistema (models) | usuario → `logs_sistema` | Entradas en log (errores/eventos) |
| Acciones en propuestas | LogPropuesta (pedidos_models) | usuario → `logpropuesta_set` | Acciones registradas en propuestas |
| Errores de pedido | LogErrorPedido (pedidos_models) | usuario → `errores_pedidos` | Errores al cargar pedidos |

---

## 3. Resumen

- **LogSistema**: ya existe; se puede usar para contar eventos/errores por usuario en un periodo.
- **No se requieren migraciones**: todas las actividades listadas usan FKs a User que ya existen.
- El reporte puede:
  1. Listar usuarios del sistema (por ejemplo, activos).
  2. Por cada usuario, mostrar un resumen de actividades (conteos por cada related_name anterior).
  3. Opcionalmente, filtrar por rango de fechas usando los campos `fecha_creacion`, `fecha_movimiento`, etc., según el modelo.

---

## 4. Implementación sugerida

- Una vista de reporte (por ejemplo, `reporte_usuarios_actividades`) que:
  - Obtenga los usuarios (ej. `User.objects.filter(is_active=True)`).
  - Para cada usuario (o por consultas agregadas por `usuario_id`), calcule los conteos de las actividades anteriores.
- Una plantilla que muestre una tabla: usuario, y columnas por cada tipo de actividad (o sección del sistema).
- Opcional: filtro por fechas y exportación a Excel.
