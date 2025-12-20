# 👥 Guía de Asignación de Roles a Usuarios

## Introducción

Esta guía te ayudará a asignar roles a usuarios en el sistema de inventario. Tienes varias opciones para hacerlo.

---

## Opción 1: Cargar Usuarios de Ejemplo (Recomendado para Empezar)

Si deseas crear rápidamente un conjunto de usuarios de ejemplo con roles predefinidos, usa este comando:

```bash
docker-compose exec web python manage.py cargar_usuarios_ejemplo
```

**Esto creará 10 usuarios de ejemplo:**

| Usuario | Email | Rol | Contraseña |
|---------|-------|-----|-----------|
| revision1 | revision@almacen.local | Revisión | revision123 |
| almacenero1 | almacenero1@almacen.local | Almacenero | almacen123 |
| almacenero2 | almacenero2@almacen.local | Almacenero | almacen123 |
| calidad1 | calidad@almacen.local | Control Calidad | calidad123 |
| facturacion1 | facturacion@almacen.local | Facturación | factura123 |
| supervision1 | supervision@almacen.local | Supervisión | supervision123 |
| logistica1 | logistica@almacen.local | Logística | logistica123 |
| recepcion1 | recepcion@almacen.local | Recepción | recepcion123 |
| conteo1 | conteo@almacen.local | Conteo | conteo123 |
| gestor1 | gestor@almacen.local | Gestor de Inventario | gestor123 |

**Ventajas:**
- ✅ Rápido y fácil
- ✅ Crea usuarios para cada rol
- ✅ Ideal para pruebas y desarrollo
- ✅ Muestra resumen con credenciales

---

## Opción 2: Crear Usuarios Interactivamente

Para crear un usuario con rol de forma interactiva:

```bash
docker-compose exec web python manage.py crear_usuario_rol
```

**El comando te pedirá:**
1. Nombre de usuario
2. Email
3. Contraseña
4. Nombre (opcional)
5. Apellido (opcional)
6. Seleccionar roles (múltiples opciones)

**Ejemplo de uso:**
```
👤 Nombre de usuario: juan_almacen
📧 Email: juan@almacen.local
🔑 Contraseña: micontraseña123
📛 Nombre: Juan
👨‍👩 Apellido: López
🎯 Roles: 1,2,3  (Revisión, Almacenero, Control Calidad)
```

---

## Opción 3: Asignar Roles a Usuarios Existentes

Si ya tienes usuarios creados y quieres asignarles roles, usa el comando `gestionar_roles`:

### Asignar un rol a un usuario

```bash
docker-compose exec web python manage.py gestionar_roles asignar --usuario=admin --rol=Administrador
```

### Asignar múltiples roles

Ejecuta el comando varias veces:

```bash
docker-compose exec web python manage.py gestionar_roles asignar --usuario=almacen1 --rol=Almacenero
docker-compose exec web python manage.py gestionar_roles asignar --usuario=almacen1 --rol=Picking
```

### Remover un rol

```bash
docker-compose exec web python manage.py gestionar_roles remover --usuario=almacen1 --rol=Almacenero
```

---

## Opción 4: Asignar Roles desde Django Admin

1. Accede a: `http://tu-servidor/admin/auth/user/`
2. Selecciona el usuario
3. En la sección "Grupos", selecciona los roles
4. Haz clic en "Guardar"

---

## Verificar Roles Asignados

### Ver roles de un usuario específico

```bash
docker-compose exec web python manage.py gestionar_roles ver-usuario --usuario=almacen1
```

**Salida esperada:**
```
👤 Información del usuario "almacen1"

  Email: almacen1@almacen.local
  Nombre: 
  Activo: Sí
  Staff: No
  Superusuario: No

📋 Roles asignados:
  • Almacenero
  • Picking

🔐 Permisos:
  (Sin permisos asignados)
```

### Listar todos los usuarios y sus roles

```bash
docker-compose exec web python manage.py gestionar_roles listar
```

---

## Casos de Uso Comunes

### Caso 1: Usuario Admin con Todos los Permisos

```bash
docker-compose exec web python manage.py gestionar_roles asignar --usuario=admin --rol=Administrador
```

### Caso 2: Usuario Almacenero que Puede Hacer Picking

```bash
docker-compose exec web python manage.py gestionar_roles asignar --usuario=almacen1 --rol=Almacenero
docker-compose exec web python manage.py gestionar_roles asignar --usuario=almacen1 --rol=Picking
```

### Caso 3: Usuario de Control de Calidad

```bash
docker-compose exec web python manage.py gestionar_roles asignar --usuario=calidad1 --rol="Control Calidad"
```

### Caso 4: Usuario de Supervisión

```bash
docker-compose exec web python manage.py gestionar_roles asignar --usuario=supervisor1 --rol=Supervisión
```

---

## Roles Disponibles

Los siguientes roles están disponibles en el sistema:

1. **Revisión** - Revisar y autorizar citas y pedidos
2. **Almacenero** - Recepción, almacenamiento y picking
3. **Control Calidad** - Inspeccionar productos
4. **Facturación** - Registrar facturas
5. **Supervisión** - Supervisar y validar operaciones
6. **Logística** - Asignación de logística y traslados
7. **Recepción** - Recepción en destino de traslados
8. **Conteo** - Realizar conteos físicos
9. **Gestor de Inventario** - Gestión general del inventario
10. **Administrador** - Administrador del sistema

---

## Troubleshooting

### Error: "Usuario no encontrado"

**Causa:** El usuario no existe en el sistema.

**Solución:** Crea el usuario primero con:
```bash
docker-compose exec web python manage.py crear_usuario_rol
```

### Error: "Rol no encontrado"

**Causa:** El rol no existe.

**Solución:** Verifica que los roles estén creados:
```bash
docker-compose exec web python manage.py gestionar_roles listar
```

Si no aparecen, crea los roles:
```bash
docker-compose exec web python manage.py crear_roles
```

### El usuario no puede acceder a una vista

**Causa:** El usuario no tiene el rol requerido.

**Solución:** 
1. Verifica qué rol tiene el usuario:
   ```bash
   docker-compose exec web python manage.py gestionar_roles ver-usuario --usuario=nombre_usuario
   ```

2. Asigna el rol correcto:
   ```bash
   docker-compose exec web python manage.py gestionar_roles asignar --usuario=nombre_usuario --rol="Nombre del Rol"
   ```

3. Cierra sesión y vuelve a iniciar sesión

---

## Flujo Recomendado

1. **Primero:** Crea los roles
   ```bash
   docker-compose exec web python manage.py crear_roles
   ```

2. **Segundo:** Carga usuarios de ejemplo (opcional)
   ```bash
   docker-compose exec web python manage.py cargar_usuarios_ejemplo
   ```

3. **Tercero:** Asigna roles a tus usuarios específicos
   ```bash
   docker-compose exec web python manage.py gestionar_roles asignar --usuario=admin --rol=Administrador
   ```

4. **Cuarto:** Verifica que todo esté correcto
   ```bash
   docker-compose exec web python manage.py gestionar_roles listar
   ```

---

**Última actualización**: Diciembre 2025
