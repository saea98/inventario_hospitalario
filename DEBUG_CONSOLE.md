# 🔍 Sistema de Debug en Consola del Navegador

Sistema de logging integrado para depuración de acceso a roles, permisos y navegación en el navegador.

---

## 🚀 Cómo Usar

### 1. Abrir la Consola del Navegador

**Chrome/Edge/Firefox:**
- Presiona `F12` o `Ctrl+Shift+I` (Windows/Linux)
- Presiona `Cmd+Option+I` (Mac)
- O haz clic derecho → Inspeccionar → Consola

### 2. Ver Comandos Disponibles

En la consola, escribe:
```javascript
debugLogger.showHelp()
```

Verás una lista de todos los comandos disponibles.

---

## 📋 Comandos Disponibles

### Logging de Acceso

#### `debugLogger.logViewAccess(viewName, allowed)`
Log cuando se accede a una vista.

```javascript
// Ejemplo: Usuario accedió a Conteo Físico
debugLogger.logViewAccess('Conteo Físico', true);

// Ejemplo: Usuario fue denegado acceso a Administración
debugLogger.logViewAccess('Administración', false);
```

#### `debugLogger.logRoleCheck(roleName, hasRole)`
Log de validación de rol.

```javascript
// Ejemplo: Usuario tiene rol Almacenero
debugLogger.logRoleCheck('Almacenero', true);

// Ejemplo: Usuario NO tiene rol Administrador
debugLogger.logRoleCheck('Administrador', false);
```

#### `debugLogger.logPermissionCheck(permissionName, hasPermission)`
Log de validación de permiso.

```javascript
// Ejemplo: Usuario tiene permiso para crear lotes
debugLogger.logPermissionCheck('inventario.add_lote', true);

// Ejemplo: Usuario NO tiene permiso para eliminar
debugLogger.logPermissionCheck('inventario.delete_lote', false);
```

#### `debugLogger.logMenuItemVisibility(menuItemName, visible)`
Log de visibilidad de items del menú.

```javascript
// Ejemplo: Conteo Físico es visible
debugLogger.logMenuItemVisibility('Conteo Físico', true);

// Ejemplo: Administración está oculta
debugLogger.logMenuItemVisibility('Administración', false);
```

#### `debugLogger.logNavigation(fromUrl, toUrl)`
Log de navegación entre páginas.

```javascript
// Ejemplo: Usuario navegó de dashboard a conteo
debugLogger.logNavigation('/dashboard/', '/logistica/conteos/buscar/');
```

#### `debugLogger.logError(errorMessage, errorDetails)`
Log de errores.

```javascript
// Ejemplo: Error al cargar datos
debugLogger.logError('Error al cargar conteos', {
    status: 403,
    message: 'Acceso denegado'
});
```

#### `debugLogger.logWarning(warningMessage, details)`
Log de advertencias.

```javascript
// Ejemplo: Advertencia de rol no encontrado
debugLogger.logWarning('Rol no configurado', {
    rol: 'Almacenista',
    esperado: 'Almacenero'
});
```

#### `debugLogger.log(message, details, level)`
Log genérico.

```javascript
// Ejemplo: Log de información
debugLogger.log('Usuario inició sesión', { username: 'almacenero2' }, 'INFO');

// Ejemplo: Log de éxito
debugLogger.log('Conteo guardado correctamente', null, 'SUCCESS');
```

---

## 📊 Visualización de Datos

### `debugLogger.showUserRolesTable()`
Muestra una tabla con los roles del usuario.

```javascript
debugLogger.showUserRolesTable();
```

**Salida esperada:**
```
┌─────────────────────┐
│ Rol                 │
├─────────────────────┤
│ Almacenero          │
│ Supervisión         │
│ Gestor de Inventario│
└─────────────────────┘
```

### `debugLogger.showMenuItemsTable()`
Muestra una tabla con los items del menú y su visibilidad.

```javascript
debugLogger.showMenuItemsTable();
```

**Salida esperada:**
```
┌──────────────────────┬─────────────────────────┬─────────┐
│ Nombre               │ URL                     │ Visible │
├──────────────────────┼─────────────────────────┼─────────┤
│ Dashboard            │ /dashboard/             │ Sí      │
│ Conteo Físico        │ /logistica/conteos/...  │ Sí      │
│ Administración       │ /admin/                 │ No      │
└──────────────────────┴─────────────────────────┴─────────┘
```

### `debugLogger.showLogs()`
Muestra el historial completo de logs.

```javascript
debugLogger.showLogs();
```

---

## 💾 Exportar y Gestionar Logs

### `debugLogger.exportLogs()`
Exporta todos los logs como JSON para compartir.

```javascript
debugLogger.exportLogs();
// Copia el JSON que aparece en la consola
```

### `debugLogger.clearLogs()`
Limpia el historial de logs.

```javascript
debugLogger.clearLogs();
```

---

## 🎯 Casos de Uso Comunes

### Caso 1: Verificar por qué un rol no ve un menú

```javascript
// 1. Ver los roles del usuario
debugLogger.showUserRolesTable();

// 2. Ver los items del menú
debugLogger.showMenuItemsTable();

// 3. Verificar si el rol específico tiene acceso
debugLogger.logRoleCheck('Almacenero', true);

// 4. Ver el historial de logs
debugLogger.showLogs();
```

### Caso 2: Rastrear navegación

```javascript
// Los logs de navegación se registran automáticamente
// Pero puedes ver el historial:
debugLogger.showLogs();

// O exportar para análisis:
debugLogger.exportLogs();
```

### Caso 3: Depurar acceso denegado

```javascript
// Cuando recibas un error de acceso denegado:
debugLogger.logError('Acceso denegado a Conteo Físico', {
    rol_usuario: 'Almacenero',
    vista_requerida: 'logistica:buscar_lote_conteo',
    decorador: '@requiere_rol'
});

// Ver todos los logs de error:
debugLogger.showLogs();
```

---

## 🎨 Colores en la Consola

El sistema usa colores para identificar fácilmente los tipos de eventos:

| Color | Tipo | Significado |
|-------|------|-------------|
| 🔵 Azul | DEBUG | Información de debug |
| 🟢 Verde | SUCCESS | Operación exitosa |
| 🟠 Naranja | WARNING | Advertencia |
| 🔴 Rojo | ERROR | Error |
| 🟣 Púrpura | ROL | Información de roles |

---

## 📝 Ejemplo Completo de Sesión de Debug

```javascript
// 1. Mostrar ayuda
debugLogger.showHelp();

// 2. Ver información del usuario
debugLogger.showUserRolesTable();

// 3. Ver items del menú
debugLogger.showMenuItemsTable();

// 4. Registrar acceso a una vista
debugLogger.logViewAccess('Conteo Físico', true);

// 5. Verificar rol
debugLogger.logRoleCheck('Almacenero', true);

// 6. Ver historial
debugLogger.showLogs();

// 7. Exportar para compartir
debugLogger.exportLogs();
```

---

## 🔧 Integración en Vistas Django

Para agregar logging automático en vistas específicas, puedes usar:

```html
<!-- En el template de la vista -->
<script>
    debugLogger.logViewAccess('Conteo Físico', true);
    debugLogger.logRoleCheck('Almacenero', true);
</script>
```

O en el contexto de Django:

```python
# En views.py
context = {
    'debug_log_view': 'Conteo Físico',
    'debug_log_allowed': True,
}
```

```html
<!-- En el template -->
{% if debug_log_view %}
<script>
    debugLogger.logViewAccess('{{ debug_log_view }}', {{ debug_log_allowed|lower }});
</script>
{% endif %}
```

---

## 🐛 Reportar Problemas

Cuando reportes un problema, incluye:

1. **Captura de pantalla** de la consola
2. **Salida de** `debugLogger.showLogs()`
3. **Salida de** `debugLogger.showUserRolesTable()`
4. **Salida de** `debugLogger.showMenuItemsTable()`

Esto ayudará a identificar rápidamente el problema.

---

## 📞 Soporte

Si encuentras un problema:

1. Abre la consola (F12)
2. Ejecuta `debugLogger.showHelp()`
3. Sigue los pasos de debug
4. Comparte los logs con el equipo de desarrollo
