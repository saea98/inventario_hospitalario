# 🚀 Guía de Implementación Rápida - Sistema de Roles

## En 5 Pasos

### Paso 1: Descargar Cambios

```bash
cd /home/ubuntu/inventario_hospitalario
git pull origin main
docker-compose restart
```

### Paso 2: Crear Roles

```bash
docker-compose exec web python manage.py crear_roles
```

**Salida esperada:**
```
✨ Total de roles en el sistema: 10
📋 Roles disponibles:
  • Administrador
  • Almacenero
  • Conteo
  • Control Calidad
  • Facturación
  • Gestor de Inventario
  • Logística
  • Recepción
  • Revisión
  • Supervisión
```

### Paso 3: Cargar Configuración de Menú

```bash
docker-compose exec web python manage.py cargar_menu_roles
```

### Paso 4: Configurar Permisos

```bash
docker-compose exec web python manage.py configurar_permisos_roles
```

### Paso 5: Crear Usuarios de Ejemplo (Opcional)

```bash
docker-compose exec web python manage.py cargar_usuarios_ejemplo
```

---

## Acceso al Dashboard

Una vez completados los pasos anteriores:

1. Accede a: `http://tu-servidor/admin-roles/`
2. Inicia sesión con usuario administrador
3. Verás el dashboard con opciones para:
   - Gestionar usuarios
   - Gestionar roles
   - Configurar menú
   - Ver reportes y estadísticas

---

## Asignar Roles a Usuarios Existentes

### Opción 1: Dashboard Web (Recomendado)

1. Accede a: `http://tu-servidor/admin-roles/usuarios/`
2. Selecciona el usuario
3. Marca los roles deseados
4. Guarda

### Opción 2: Comando de Línea

```bash
docker-compose exec web python manage.py gestionar_roles asignar \
  --usuario=admin \
  --rol=Administrador
```

### Opción 3: Django Admin

1. Accede a: `http://tu-servidor/admin/auth/user/`
2. Selecciona el usuario
3. En "Grupos", selecciona los roles
4. Guarda

---

## Verificar Configuración

### Ver Roles de un Usuario

```bash
docker-compose exec web python manage.py gestionar_roles ver-usuario --usuario=admin
```

### Ver Todos los Roles

```bash
docker-compose exec web python manage.py gestionar_roles listar
```

### Ver Matriz de Acceso

Accede a: `http://tu-servidor/admin-roles/reporte-acceso/`

---

## Próximos Pasos

1. **Asigna roles a tus usuarios** según sus funciones
2. **Configura el menú** desde el dashboard si necesitas cambios
3. **Prueba con diferentes usuarios** para verificar el acceso
4. **Lee la documentación completa** para entender todas las opciones

---

## Documentación

- **DOCUMENTACION_SISTEMA_ROLES.md** - Documentación completa
- **GUIA_ROLES.md** - Guía básica
- **GUIA_CONTROL_ACCESO.md** - Control de acceso en vistas

---

## Soporte

Si tienes problemas:

1. Verifica que todos los comandos se ejecutaron sin errores
2. Limpia el caché del navegador (Ctrl+Shift+Del)
3. Cierra sesión y vuelve a iniciar sesión
4. Revisa la sección de Troubleshooting en DOCUMENTACION_SISTEMA_ROLES.md

---

**¡Listo!** Tu sistema de roles está configurado y funcionando. 🎉
