# 🔄 Guía de Migraciones - Entorno de Calidad

## 🎯 Objetivo
Este documento contiene los comandos necesarios para ejecutar las migraciones en tu entorno de calidad de AWS.

---

## ⚠️ Problema Actual

```
ProgrammingError: relation "inventario_menuitemrol" does not exist
```

**Causa:** Las migraciones no han sido ejecutadas en la base de datos de calidad.

---

## 🚀 Solución Rápida

En tu servidor de calidad, ejecuta estos comandos en orden:

### 1️⃣ Descargar los cambios más recientes
```bash
cd /ruta/a/tu/proyecto
git pull origin main
```

### 2️⃣ Ejecutar las migraciones
```bash
docker-compose exec web python manage.py migrate
```

**Salida esperada:**
```
Operations to perform:
  Apply all migrations: admin, auth, contenttypes, inventario, sessions, ...
Running migrations:
  Applying inventario.0029_menuitemrol
  Applying inventario.0030_menuitemrol_roles
  Applying inventario.0031_alter_menuitemrol_options
  ... (más migraciones)
```

### 3️⃣ Cargar datos iniciales (Roles, Usuarios, Menú)
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

### 4️⃣ Reiniciar contenedores
```bash
docker-compose restart
```

---

## 📋 Comandos Detallados

### Ver estado de migraciones
```bash
docker-compose exec web python manage.py showmigrations
```

**Esto mostrará:**
- ✅ Migraciones aplicadas (con marca de verificación)
- ⚠️ Migraciones pendientes (sin marca)

### Ver migraciones de inventario específicamente
```bash
docker-compose exec web python manage.py showmigrations inventario
```

### Aplicar solo las migraciones de inventario
```bash
docker-compose exec web python manage.py migrate inventario
```

### Ver detalles de una migración específica
```bash
docker-compose exec web python manage.py sqlmigrate inventario 0029
```

---

## 🔙 Revertir Migraciones (Si es necesario)

⚠️ **CUIDADO:** Esto eliminará datos. Solo usar en desarrollo.

```bash
# Revertir la última migración
docker-compose exec web python manage.py migrate inventario 0028

# Revertir todas las migraciones de inventario
docker-compose exec web python manage.py migrate inventario zero
```

---

## ✅ Verificación Posterior

Después de ejecutar las migraciones, verifica que todo funcionó:

### 1. Verificar que la tabla existe
```bash
docker-compose exec web python manage.py shell
```

Luego en la consola:
```python
from inventario.models import MenuItemRol
print(f"Total de opciones de menú: {MenuItemRol.objects.count()}")
```

### 2. Verificar que los roles fueron creados
```bash
docker-compose exec web python manage.py gestionar_roles listar
```

### 3. Verificar que los usuarios fueron creados
```bash
docker-compose exec web python manage.py shell
```

Luego:
```python
from inventario.models import User
print(f"Total de usuarios: {User.objects.count()}")
for usuario in User.objects.all():
    print(f"  - {usuario.username}")
```

### 4. Acceder a la aplicación
```
URL: http://tu-servidor-aws:8700/
Usuario: almacenero1
Contraseña: almacen123
```

---

## 📊 Migraciones Principales Creadas

| Migración | Descripción |
|-----------|-------------|
| 0029_menuitemrol | Crear modelo MenuItemRol |
| 0030_menuitemrol_roles | Agregar relación con roles |
| 0031_alter_menuitemrol_options | Opciones del modelo |

---

## 🛠️ Troubleshooting

### Error: "Migración ya aplicada"
**Solución:** Es normal, solo significa que ya fue aplicada. Continúa con el siguiente paso.

### Error: "No migrations to apply"
**Solución:** Todas las migraciones ya están aplicadas. Verifica que los datos iniciales fueron cargados.

### Error: "Tabla no existe"
**Solución:** Ejecuta las migraciones nuevamente:
```bash
docker-compose exec web python manage.py migrate --run-syncdb
```

### Error: "Permiso denegado"
**Solución:** Asegúrate de tener permisos en la base de datos. Verifica las credenciales en `.env`

---

## 📝 Secuencia Completa Recomendada

```bash
# 1. Descargar cambios
git pull origin main

# 2. Ejecutar migraciones
docker-compose exec web python manage.py migrate

# 3. Crear roles
docker-compose exec web python manage.py crear_roles

# 4. Crear usuarios
docker-compose exec web python manage.py cargar_usuarios_ejemplo

# 5. Cargar configuración del menú
docker-compose exec web python manage.py cargar_menu_roles

# 6. Configurar permisos
docker-compose exec web python manage.py configurar_permisos_roles

# 7. Reiniciar
docker-compose restart

# 8. Verificar
docker-compose exec web python manage.py gestionar_roles listar
```

---

## 📞 Soporte

Si tienes problemas:

1. Verifica que Docker está corriendo: `docker-compose ps`
2. Revisa los logs: `docker-compose logs web`
3. Reinicia los contenedores: `docker-compose restart`
4. Ejecuta las migraciones nuevamente: `docker-compose exec web python manage.py migrate`

---

**Última actualización:** Diciembre 2025
**Versión:** 1.0
