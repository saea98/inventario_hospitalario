# ✅ Opción 2: Marcar Migraciones como Aplicadas (RECOMENDADO)

## 🎯 Objetivo

Marcar las migraciones que ya fueron aplicadas como "fake" (sin ejecutarlas), para que Django no intente crearlas nuevamente. Esto preserva todos los datos existentes.

---

## ⚠️ Importante

Esta opción es **SEGURA** porque:
- ✅ No elimina datos
- ✅ No modifica tablas existentes
- ✅ Solo marca migraciones en la tabla `django_migrations`
- ✅ Permite que las nuevas migraciones se ejecuten correctamente

---

## 🚀 Pasos Exactos

### Paso 1: Ver el estado actual de migraciones

```bash
docker-compose exec web python manage.py showmigrations inventario
```

**Salida esperada:**
```
inventario
 [ ] 0001_initial
 [ ] 0002_...
 [X] 0023_itempropuesta_loteasignado_propuestapedido_and_more
 [X] 0024_llegadaproveedor_itemllegada_documentollegada_and_more
 [ ] 0025_merge_20251218_1327
 [ ] 0026_devolucion_proveedor
 [ ] 0027_create_devolucion_tables
 [ ] 0028_create_roles
 [ ] 0029_add_menu_item_rol
 [ ] 0030_merge_migrations
```

**Nota:** Las marcadas con `[X]` ya están aplicadas. Las marcadas con `[ ]` están pendientes.

---

### Paso 2: Marcar migraciones como aplicadas (fake)

Ejecuta este comando para marcar todas las migraciones hasta la 0027 como aplicadas sin ejecutarlas:

```bash
docker-compose exec web python manage.py migrate --fake inventario 0027
```

**Salida esperada:**
```
Operations to perform:
  Target specific migration: 0027_create_devolucion_tables, from inventario
Running migrations:
  Faking migration inventario.0001_initial
  Faking migration inventario.0002_...
  ... (todas las migraciones hasta 0027)
```

---

### Paso 3: Ejecutar las nuevas migraciones

Ahora ejecuta las migraciones nuevas (0028, 0029, 0030):

```bash
docker-compose exec web python manage.py migrate
```

**Salida esperada:**
```
Operations to perform:
  Apply all migrations: admin, auth, contenttypes, inventario, sessions, ...
Running migrations:
  Applying inventario.0028_create_roles
  Applying inventario.0029_add_menu_item_rol
  Applying inventario.0030_merge_migrations
```

---

### Paso 4: Verificar que todo está correcto

```bash
docker-compose exec web python manage.py showmigrations inventario
```

**Salida esperada:**
```
inventario
 [X] 0001_initial
 [X] 0002_...
 [X] 0023_itempropuesta_loteasignado_propuestapedido_and_more
 [X] 0024_llegadaproveedor_itemllegada_documentollegada_and_more
 [X] 0025_merge_20251218_1327
 [X] 0026_devolucion_proveedor
 [X] 0027_create_devolucion_tables
 [X] 0028_create_roles
 [X] 0029_add_menu_item_rol
 [X] 0030_merge_migrations
```

Todas deberían estar marcadas con `[X]`.

---

### Paso 5: Cargar datos iniciales

Ahora ejecuta los comandos para crear roles, usuarios y configuración:

```bash
# Crear roles
docker-compose exec web python manage.py crear_roles

# Crear usuarios de ejemplo
docker-compose exec web python manage.py cargar_usuarios_ejemplo

# Cargar configuración del menú
docker-compose exec web python manage.py cargar_menu_roles

# Configurar permisos por rol
docker-compose exec web python manage.py configurar_permisos_roles
```

---

### Paso 6: Reiniciar contenedores

```bash
docker-compose restart
```

---

### Paso 7: Verificar que funciona

Accede a la aplicación:
```
URL: http://tu-servidor:8700/
Usuario: almacenero1
Contraseña: almacen123
```

Verifica que:
- ✅ El menú se muestra correctamente
- ✅ Los roles están configurados
- ✅ Los usuarios pueden iniciar sesión
- ✅ Los datos de prueba anteriores siguen existiendo

---

## 📋 Resumen de Comandos

Si quieres ejecutar todo de una vez:

```bash
# 1. Marcar migraciones como aplicadas
docker-compose exec web python manage.py migrate --fake inventario 0027

# 2. Ejecutar nuevas migraciones
docker-compose exec web python manage.py migrate

# 3. Crear roles
docker-compose exec web python manage.py crear_roles

# 4. Crear usuarios
docker-compose exec web python manage.py cargar_usuarios_ejemplo

# 5. Cargar menú
docker-compose exec web python manage.py cargar_menu_roles

# 6. Configurar permisos
docker-compose exec web python manage.py configurar_permisos_roles

# 7. Reiniciar
docker-compose restart
```

---

## 🛠️ Troubleshooting

### Error: "Target migration 0027 not found"

**Solución:** Verifica que el nombre de la migración es correcto:
```bash
docker-compose exec web python manage.py showmigrations inventario | grep 0027
```

### Error: "Migration already applied"

**Solución:** Es normal si ya fue marcada. Continúa con el siguiente paso.

### Las migraciones se quedan "stuck"

**Solución:** Reinicia los contenedores:
```bash
docker-compose restart
docker-compose exec web python manage.py migrate
```

### Los datos anteriores desaparecieron

**Solución:** No debería suceder con esta opción. Si pasó:
1. Verifica que usaste `--fake`
2. Restaura desde backup si es necesario
3. Contacta al equipo de soporte

---

## ✅ Ventajas de esta Opción

✅ Preserva todos los datos existentes
✅ No modifica tablas
✅ Rápida de ejecutar
✅ Segura y reversible
✅ Ideal para ambientes de calidad

---

## 📞 Soporte

Si tienes problemas:

1. Verifica que Docker está corriendo: `docker-compose ps`
2. Revisa los logs: `docker-compose logs web`
3. Ejecuta `showmigrations` para ver el estado actual
4. Intenta nuevamente

---

**Última actualización:** Diciembre 2025
**Versión:** 1.0
