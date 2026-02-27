# Consultas SQL: reservas y disponibilidad

## 1. Reserva real vs campo `cantidad_reservada` (desincronización)

El reporte **reportes/salidas/reservas** usa **LoteAsignado** (surtido=False).  
Si en ese reporte no aparecen reservas para una clave pero en `inventario_loteubicacion` el campo `cantidad_reservada` > 0, hay desincronización.

Esta consulta compara, por cada `LoteUbicacion`, el campo `cantidad_reservada` con la suma real de asignaciones no surtidas:

```sql
-- Comparar cantidad_reservada (campo) vs reserva real (suma de LoteAsignado con surtido=False)
-- Filas donde no coinciden indican desincronización.
SELECT
    lu.id AS lote_ubicacion_id,
    l.numero_lote,
    u.codigo AS ubicacion_codigo,
    p.clave_cnis,
    lu.cantidad,
    lu.cantidad_reservada AS campo_reservada,
    COALESCE(SUM(la.cantidad_asignada) FILTER (WHERE la.surtido = false), 0)::int AS reserva_real_loteasignado,
    lu.cantidad - lu.cantidad_reservada AS disp_usando_campo,
    lu.cantidad - COALESCE(SUM(la.cantidad_asignada) FILTER (WHERE la.surtido = false), 0)::int AS disp_usando_real
FROM inventario_loteubicacion lu
JOIN inventario_lote l ON lu.lote_id = l.id
JOIN inventario_ubicacionalmacen u ON lu.ubicacion_id = u.id
JOIN inventario_producto p ON l.producto_id = p.id
LEFT JOIN inventario_loteasignado la ON la.lote_ubicacion_id = lu.id
WHERE p.clave_cnis = '060.506.4492'
  AND l.fecha_caducidad >= CURRENT_DATE
  AND l.estado = 1
  AND lu.cantidad > 0
GROUP BY lu.id, l.numero_lote, u.codigo, p.clave_cnis, lu.cantidad, lu.cantidad_reservada
ORDER BY l.fecha_caducidad, l.numero_lote, u.codigo;
```

- **PostgreSQL**: la sintaxis `SUM(...) FILTER (WHERE ...)` es válida.
- **MySQL**: usar en su lugar:
  `SUM(CASE WHEN la.surtido = 0 THEN la.cantidad_asignada ELSE 0 END)` en lugar de `SUM(la.cantidad_asignada) FILTER (WHERE la.surtido = false)`.

Si en tu motor no existe `FILTER`, usa esta variante (válida en PostgreSQL y MySQL):

```sql
SELECT
    lu.id,
    l.numero_lote,
    u.codigo,
    p.clave_cnis,
    lu.cantidad,
    lu.cantidad_reservada AS campo_reservada,
    COALESCE(SUM(CASE WHEN la.surtido = false THEN la.cantidad_asignada ELSE 0 END), 0)::int AS reserva_real
FROM inventario_loteubicacion lu
JOIN inventario_lote l ON lu.lote_id = l.id
JOIN inventario_ubicacionalmacen u ON lu.ubicacion_id = u.id
JOIN inventario_producto p ON l.producto_id = p.id
LEFT JOIN inventario_loteasignado la ON la.lote_ubicacion_id = lu.id AND la.surtido = false
WHERE p.clave_cnis = '060.506.4492'
  AND l.fecha_caducidad >= CURRENT_DATE
  AND l.estado = 1
  AND lu.cantidad > 0
GROUP BY lu.id, l.numero_lote, u.codigo, p.clave_cnis, lu.cantidad, lu.cantidad_reservada;
```

(En MySQL puede ser `surtido = 0` y quitar el `::int` si no lo soporta.)

---

## 2. Query que usa la vista para el dropdown (disponible = cantidad − reserva real)

La vista de edición de propuesta usa **reserva real** = suma de `LoteAsignado.cantidad_asignada` donde `surtido = False` (misma lógica que el reporte de reservas). Equivalente en SQL:

```sql
SELECT
    lu.id AS lote_ubicacion_id,
    l.numero_lote,
    l.fecha_caducidad,
    u.codigo AS ubicacion_codigo,
    lu.cantidad,
    COALESCE(SUM(la.cantidad_asignada) FILTER (WHERE la.surtido = false), 0)::int AS reservado_real,
    lu.cantidad - COALESCE(SUM(la.cantidad_asignada) FILTER (WHERE la.surtido = false), 0)::int AS disponible
FROM inventario_loteubicacion lu
INNER JOIN inventario_lote l ON lu.lote_id = l.id
INNER JOIN inventario_ubicacionalmacen u ON lu.ubicacion_id = u.id
LEFT JOIN inventario_loteasignado la ON la.lote_ubicacion_id = lu.id
WHERE l.producto_id = (SELECT id FROM inventario_producto WHERE clave_cnis = '060.506.4492' LIMIT 1)
  AND l.fecha_caducidad >= CURRENT_DATE
  AND l.estado = 1
  AND lu.cantidad > 0
GROUP BY lu.id, l.id, l.numero_lote, l.fecha_caducidad, u.codigo, lu.cantidad
HAVING lu.cantidad - COALESCE(SUM(la.cantidad_asignada) FILTER (WHERE la.surtido = false), 0)::int > 0
ORDER BY l.fecha_caducidad, l.numero_lote, u.codigo;
```

Variante sin `FILTER` (CASE WHEN):

```sql
LEFT JOIN inventario_loteasignado la ON la.lote_ubicacion_id = lu.id AND la.surtido = false
...
COALESCE(SUM(la.cantidad_asignada), 0)::int AS reservado_real,
...
HAVING lu.cantidad - COALESCE(SUM(la.cantidad_asignada), 0)::int > 0
```

Con esto puedes verificar en la base de datos qué devuelve la lógica de la vista y contrastar con el reporte de reservas.
