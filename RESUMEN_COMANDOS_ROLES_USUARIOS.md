# 📋 Resumen de Comandos - Crear Roles y Usuarios

## 🎯 Objetivo
Este documento contiene todos los comandos necesarios para crear roles y usuarios en tu entorno de calidad de AWS.

---

## 🚀 Pasos Previos

### 1. Descargar los cambios más recientes
```bash
cd /ruta/a/tu/proyecto
git pull origin main
```

### 2. Reiniciar los contenedores
```bash
docker-compose restart
```

---

## 👥 Crear Roles del Sistema

### Comando: Crear todos los roles
```bash
docker-compose exec web python manage.py crear_roles
```

**Salida esperada:**
```
🔄 Creando roles del sistema...

✅ Rol "Revisión" creado
✅ Rol "Almacenero" creado
✅ Rol "Control Calidad" creado
✅ Rol "Facturación" creado
✅ Rol "Supervisión" creado
✅ Rol "Logística" creado
✅ Rol "Recepción" creado
✅ Rol "Conteo" creado
✅ Rol "Gestor de Inventario" creado
✅ Rol "Administrador" creado

✨ Total de roles en el sistema: 10
```

---

## 👤 Crear Usuarios de Ejemplo

### Comando: Cargar usuarios de ejemplo (RECOMENDADO)
```bash
docker-compose exec web python manage.py cargar_usuarios_ejemplo
```

**Esto crea 10 usuarios automáticamente:**

| Usuario | Rol | Contraseña |
|---------|-----|-----------|
| revision1 | Revisión | revision123 |
| almacenero1 | Almacenero | almacen123 |
| almacenero2 | Almacenero | almacen123 |
| calidad1 | Control Calidad | calidad123 |
| facturacion1 | Facturación | factura123 |
| supervision1 | Supervisión | supervision123 |
| logistica1 | Logística | logistica123 |
| recepcion1 | Recepción | recepcion123 |
| conteo1 | Conteo | conteo123 |
| gestor1 | Gestor de Inventario | gestor123 |

---

## 🔧 Gestionar Roles Manualmente

### Listar todos los roles
```bash
docker-compose exec web python manage.py gestionar_roles listar
```

### Asignar un rol a un usuario existente
```bash
docker-compose exec web python manage.py gestionar_roles asignar --usuario=admin --rol=Administrador
```

### Remover un rol de un usuario
```bash
docker-compose exec web python manage.py gestionar_roles remover --usuario=admin --rol=Administrador
```

### Ver información de un usuario (roles y permisos)
```bash
docker-compose exec web python manage.py gestionar_roles ver-usuario --usuario=admin
```

### Eliminar un rol del sistema
```bash
docker-compose exec web python manage.py gestionar_roles eliminar --rol="Nombre del Rol"
```

---

## 📋 Cargar Configuración del Menú

### Comando: Cargar configuración de menú por roles
```bash
docker-compose exec web python manage.py cargar_menu_roles
```

**Esto configura automáticamente:**
- ✅ Qué opciones de menú ve cada rol
- ✅ Qué subopciones están disponibles
- ✅ Permisos de acceso granulares

---

## 🔐 Configurar Permisos por Rol

### Comando: Configurar permisos específicos
```bash
docker-compose exec web python manage.py configurar_permisos_roles
```

**Esto asigna permisos granulares a cada rol**

---

## 📊 Verificar Configuración

### Ver todos los roles creados
```bash
docker-compose exec web python manage.py shell
```

Luego en la consola de Django:
```python
from django.contrib.auth.models import Group
for grupo in Group.objects.all():
    print(f"- {grupo.name}")
```

### Ver todos los usuarios
```bash
docker-compose exec web python manage.py shell
```

Luego en la consola de Django:
```python
from inventario.models import User
for usuario in User.objects.all():
    print(f"- {usuario.username} ({usuario.email})")
```

### Ver roles de un usuario específico
```bash
docker-compose exec web python manage.py shell
```

Luego en la consola de Django:
```python
from inventario.models import User
usuario = User.objects.get(username='almacenero1')
print(f"Roles: {[g.name for g in usuario.groups.all()]}")
```

---

## 🎯 Secuencia Completa Recomendada

Para un setup completo en tu entorno de calidad, ejecuta en este orden:

```bash
# 1. Descargar cambios
git pull origin main
docker-compose restart

# 2. Crear roles
docker-compose exec web python manage.py crear_roles

# 3. Cargar usuarios de ejemplo
docker-compose exec web python manage.py cargar_usuarios_ejemplo

# 4. Cargar configuración del menú
docker-compose exec web python manage.py cargar_menu_roles

# 5. Configurar permisos por rol
docker-compose exec web python manage.py configurar_permisos_roles

# 6. Verificar que todo está correcto
docker-compose exec web python manage.py gestionar_roles listar
```

---

## 🌐 Acceder a la Aplicación

### URL de Acceso
```
http://tu-servidor-aws:8700/
```

### Usuarios para Pruebas

**Administrador:**
- Usuario: `admin`
- Contraseña: (la que ya tienes)

**Usuarios de Ejemplo:**
- Usuario: `almacenero1`
- Contraseña: `almacen123`

(Ver tabla arriba para otros usuarios)

---

## 🛠️ Troubleshooting

### Error: "Comando no encontrado"
**Solución:** Asegúrate de estar dentro del contenedor Docker
```bash
docker-compose exec web python manage.py [comando]
```

### Error: "Rol no encontrado"
**Solución:** Ejecuta primero el comando para crear roles
```bash
docker-compose exec web python manage.py crear_roles
```

### Error: "Usuario ya existe"
**Solución:** El usuario ya fue creado. Puedes asignarle más roles
```bash
docker-compose exec web python manage.py gestionar_roles asignar --usuario=almacenero1 --rol="Otro Rol"
```

### Los cambios no se ven en el menú
**Solución:** Limpia el caché del navegador (Ctrl+Shift+Del) y recarga la página

---

## 📞 Soporte

Si tienes problemas con los comandos:

1. Verifica que Docker está corriendo
2. Verifica que estás en el directorio correcto
3. Revisa los logs: `docker-compose logs web`
4. Reinicia los contenedores: `docker-compose restart`

---

**Última actualización:** Diciembre 2025
**Versión:** 1.0
