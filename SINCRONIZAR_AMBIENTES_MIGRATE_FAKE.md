# Sincronizar Ambientes con migrate --fake

## Problema

Los ambientes tienen diferentes historiales de migraciones:
- **Producción**: Tiene todas las migraciones incluyendo las merge
- **Desarrollo y Calidad**: Les faltan algunas migraciones merge

## Solución: migrate --fake

En lugar de copiar todas las migraciones merge, vamos a usar `migrate --fake` para marcar como aplicadas todas las migraciones que ya están en la BD.

---

## ⚠️ IMPORTANTE: Hacer Backup Primero

Antes de ejecutar cualquier comando, **HAGAN BACKUP DE LAS BASES DE DATOS**:

```bash
# DESARROLLO
docker exec -it inventario_dev pg_dump -U postgres inventario_hospitalario > backup_dev_$(date +%Y%m%d_%H%M%S).sql

# CALIDAD
docker exec -it inventario_qa pg_dump -U postgres inventario_hospitalario > backup_qa_$(date +%Y%m%d_%H%M%S).sql

# PRODUCCIÓN
docker exec -it inventario_dev_2 pg_dump -U postgres inventario_hospitalario > backup_prod_$(date +%Y%m%d_%H%M%S).sql
```

---

## 🔄 PASO 1: Pull en TODOS los ambientes

```bash
# DESARROLLO
cd ~/inventario/inventario_hospitalario
git pull origin main

# CALIDAD
cd ~/inventario/inventario_hospitalario
git pull origin main

# PRODUCCIÓN
cd ~/inventario/inventario_hospitalario_nuevo
git pull origin main
```

---

## 🔄 PASO 2: Sincronizar con migrate --fake

### DESARROLLO

```bash
# 1. Entrar al directorio
cd ~/inventario/inventario_hospitalario

# 2. Marcar todas las migraciones como aplicadas (sin ejecutarlas)
docker exec -it inventario_dev python manage.py migrate --fake inventario

# 3. Verificar que todas estén marcadas
docker exec -it inventario_dev python manage.py showmigrations inventario

# 4. Reiniciar contenedor
docker-compose restart web

# 5. Verificar estado
docker exec -it inventario_dev python manage.py check
```

### CALIDAD

```bash
# 1. Entrar al directorio
cd ~/inventario/inventario_hospitalario

# 2. Marcar todas las migraciones como aplicadas (sin ejecutarlas)
docker exec -it inventario_qa python manage.py migrate --fake inventario

# 3. Verificar que todas estén marcadas
docker exec -it inventario_qa python manage.py showmigrations inventario

# 4. Reiniciar contenedor
docker-compose restart web

# 5. Verificar estado
docker exec -it inventario_qa python manage.py check
```

### PRODUCCIÓN

```bash
# Solo verificar que todo esté bien
cd ~/inventario/inventario_hospitalario_nuevo

# Verificar migraciones
docker exec -it inventario_dev_2 python manage.py showmigrations inventario

# Verificar estado
docker exec -it inventario_dev_2 python manage.py check
```

---

## 📋 Explicación de migrate --fake

**`migrate --fake`** marca las migraciones como aplicadas en la tabla `django_migrations` SIN ejecutar las operaciones SQL.

**¿Por qué usamos esto?**
- Las migraciones ya están aplicadas en la BD (las tablas ya existen)
- Solo necesitamos que Django sepa que están aplicadas
- No queremos ejecutar las operaciones SQL nuevamente

**Resultado:**
```
[X] 0001_initial
[X] 0002_agregar_dashboard_movimientos_menu
...
[X] 0043_cargainventario_productos_no_procesados
[X] 0043_merge_20260107_1854
[X] 0044_merge_20260110_1719
[X] 0045_logpropuesta
```

---

## ✅ Verificación Final

Después de ejecutar los comandos, en TODOS los ambientes deberías ver:

```bash
docker exec -it inventario_dev python manage.py showmigrations inventario
```

**Resultado esperado:**
```
inventario
 [X] 0001_initial
 [X] 0002_agregar_dashboard_movimientos_menu
 [X] 0002_alter_lote_fecha_caducidad
 ...
 [X] 0043_cargainventario_productos_no_procesados
 [X] 0043_merge_20260107_1854
 [X] 0044_merge_20260110_1719
 [X] 0045_logpropuesta
```

Todas con **[X]** (aplicadas)

---

## 🚨 Si Algo Sale Mal

### Revertir cambios

```bash
# Ver el backup que creaste
ls -la backup_*.sql

# Restaurar la BD
docker exec -i inventario_dev psql -U postgres inventario_hospitalario < backup_dev_YYYYMMDD_HHMMSS.sql

# Reiniciar contenedor
docker-compose restart web
```

### Deshacer migrate --fake

```bash
# Revertir a una migración anterior
docker exec -it inventario_dev python manage.py migrate inventario 0042

# Luego intentar de nuevo
```

---

## 📝 Checklist

- [ ] Hice backup de las BDs
- [ ] Hice pull en los 3 ambientes
- [ ] Ejecuté `migrate --fake` en desarrollo
- [ ] Ejecuté `migrate --fake` en calidad
- [ ] Verifiqué con `showmigrations` en los 3 ambientes
- [ ] Todos muestran [X] en todas las migraciones
- [ ] Ejecuté `check` sin errores críticos
- [ ] Reinicié los contenedores

---

## 🎯 Resultado Final

Después de esto:
- ✅ Todos los ambientes sincronizados
- ✅ Tabla `LogPropuesta` disponible
- ✅ Funcionalidad de liberación de propuestas lista
- ✅ Sin conflictos de migraciones
- ✅ Listos para futuros deployments

---

## Comandos Rápidos (Copiar y Pegar)

### DESARROLLO
```bash
cd ~/inventario/inventario_hospitalario
git pull origin main
docker exec -it inventario_dev python manage.py migrate --fake inventario
docker exec -it inventario_dev python manage.py showmigrations inventario
docker-compose restart web
docker exec -it inventario_dev python manage.py check
```

### CALIDAD
```bash
cd ~/inventario/inventario_hospitalario
git pull origin main
docker exec -it inventario_qa python manage.py migrate --fake inventario
docker exec -it inventario_qa python manage.py showmigrations inventario
docker-compose restart web
docker exec -it inventario_qa python manage.py check
```

### PRODUCCIÓN
```bash
cd ~/inventario/inventario_hospitalario_nuevo
git pull origin main
docker exec -it inventario_dev_2 python manage.py showmigrations inventario
docker exec -it inventario_dev_2 python manage.py check
```

---

## Preguntas Frecuentes

**P: ¿Es seguro usar migrate --fake?**
R: Sí, es seguro. Solo marca en la BD que las migraciones fueron aplicadas. No modifica datos.

**P: ¿Qué pasa si ejecuto migrate --fake dos veces?**
R: No pasa nada. Django detecta que ya están marcadas y no hace nada.

**P: ¿Necesito reiniciar después de migrate --fake?**
R: No es obligatorio, pero es recomendable para evitar problemas de caché.

**P: ¿Puedo hacer rollback después de migrate --fake?**
R: Sí, con `migrate inventario 0042` por ejemplo.

**P: ¿Qué pasa con los datos existentes?**
R: No se afectan. `migrate --fake` solo actualiza la tabla `django_migrations`.
