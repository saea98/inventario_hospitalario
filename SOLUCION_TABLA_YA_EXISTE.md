# 🔧 Solución: Tabla Ya Existe

## 🎯 Problema

```
ProgrammingError: relation "inventario_itempropuesta" already exists
```

**Causa:** Algunas migraciones ya fueron aplicadas parcialmente en tu base de datos de calidad.

---

## ✅ Soluciones

### Opción 1: Limpiar y Reiniciar (RECOMENDADO para Calidad)

⚠️ **ADVERTENCIA:** Esto eliminará TODOS los datos de la base de datos.

```bash
# 1. Conectar a PostgreSQL
docker-compose exec db psql -U inventario -d inventario_db -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

# 2. Ejecutar migraciones desde cero
docker-compose exec web python manage.py migrate

# 3. Cargar datos iniciales
docker-compose exec web python manage.py crear_roles
docker-compose exec web python manage.py cargar_usuarios_ejemplo
docker-compose exec web python manage.py cargar_menu_roles
docker-compose exec web python manage.py configurar_permisos_roles

# 4. Reiniciar
docker-compose restart
```

---

### Opción 2: Marcar Migraciones como Aplicadas

Si no quieres perder datos, puedes marcar las migraciones como ya aplicadas:

```bash
# Ver qué migraciones están aplicadas
docker-compose exec web python manage.py showmigrations inventario

# Marcar migraciones como aplicadas (sin ejecutarlas)
docker-compose exec web python manage.py migrate --fake inventario 0027

# Luego ejecutar las nuevas migraciones
docker-compose exec web python manage.py migrate
```

---

### Opción 3: Revertir a Cero y Reiniciar

```bash
# Revertir todas las migraciones de inventario
docker-compose exec web python manage.py migrate inventario zero --fake

# Ejecutar todas las migraciones
docker-compose exec web python manage.py migrate

# Cargar datos
docker-compose exec web python manage.py crear_roles
docker-compose exec web python manage.py cargar_usuarios_ejemplo
docker-compose exec web python manage.py cargar_menu_roles
docker-compose exec web python manage.py configurar_permisos_roles

# Reiniciar
docker-compose restart
```

---

## 🎯 Recomendación

Para tu entorno de **CALIDAD**, te recomiendo la **Opción 1** (Limpiar y Reiniciar):

1. Es un entorno de prueba, no hay datos importantes
2. Garantiza que todo esté limpio y consistente
3. Evita conflictos futuros

---

## 📋 Pasos Detallados (Opción 1)

### Paso 1: Conectar a PostgreSQL y limpiar
```bash
docker-compose exec db psql -U inventario -d inventario_db
```

Luego ejecuta:
```sql
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
\q
```

O en una sola línea:
```bash
docker-compose exec db psql -U inventario -d inventario_db -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
```

### Paso 2: Ejecutar migraciones
```bash
docker-compose exec web python manage.py migrate
```

**Salida esperada:**
```
Operations to perform:
  Apply all migrations: admin, auth, contenttypes, inventario, sessions, ...
Running migrations:
  Applying inventario.0001_initial
  Applying inventario.0002_...
  ... (todas las migraciones)
  Applying inventario.0030_merge_migrations
```

### Paso 3: Cargar datos iniciales
```bash
docker-compose exec web python manage.py crear_roles
docker-compose exec web python manage.py cargar_usuarios_ejemplo
docker-compose exec web python manage.py cargar_menu_roles
docker-compose exec web python manage.py configurar_permisos_roles
```

### Paso 4: Reiniciar
```bash
docker-compose restart
```

### Paso 5: Verificar
```bash
# Acceder a la aplicación
# URL: http://tu-servidor:8700/
# Usuario: almacenero1
# Contraseña: almacen123
```

---

## 🛠️ Troubleshooting

### Error: "Permission denied"
**Solución:** Asegúrate de tener permisos en PostgreSQL. Verifica las credenciales en `.env`

### Error: "Database does not exist"
**Solución:** Crea la base de datos primero:
```bash
docker-compose exec db psql -U postgres -c "CREATE DATABASE inventario_db;"
```

### Las migraciones se quedan "stuck"
**Solución:** Reinicia los contenedores:
```bash
docker-compose restart
docker-compose exec web python manage.py migrate
```

---

## 📞 Soporte

Si tienes más problemas:

1. Verifica que Docker está corriendo: `docker-compose ps`
2. Revisa los logs: `docker-compose logs web`
3. Reinicia todo: `docker-compose restart`
4. Intenta nuevamente

---

**Última actualización:** Diciembre 2025
**Versión:** 1.0
