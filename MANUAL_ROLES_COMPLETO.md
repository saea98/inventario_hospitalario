# 📚 Manual Completo de Roles del Sistema de Inventario IMSS-Bienestar

**Última actualización**: Diciembre 2025  
**Versión**: 1.0  
**Estado**: Producción

---

## 📋 Tabla de Contenidos

1. [Introducción](#introducción)
2. [Roles del Sistema](#roles-del-sistema)
3. [Matriz de Permisos](#matriz-de-permisos)
4. [Descripción Detallada de Cada Rol](#descripción-detallada-de-cada-rol)
5. [Flujos de Trabajo por Rol](#flujos-de-trabajo-por-rol)
6. [Pruebas de Acceso](#pruebas-de-acceso)

---

## Introducción

El sistema de inventario IMSS-Bienestar utiliza un modelo de control de acceso basado en **roles**. Cada usuario puede tener uno o más roles asignados, y cada rol determina qué funcionalidades puede ver y usar.

### Principios Clave

- ✅ **Seguridad**: Cada rol solo ve lo que necesita ver
- ✅ **Flexibilidad**: Los usuarios pueden tener múltiples roles
- ✅ **Auditoría**: Todos los accesos se registran por rol
- ✅ **Escalabilidad**: Nuevos roles se pueden agregar sin modificar código

---

## Roles del Sistema

El sistema cuenta con **10 roles principales**:

| # | Rol | Tipo | Descripción |
|---|-----|------|-------------|
| 1 | **Administrador** | Sistema | Control total del sistema, gestión de usuarios y roles |
| 2 | **Gestor de Inventario** | Operativo | Gestión general del inventario, reportes y análisis |
| 3 | **Almacenero** | Operativo | Recepción, almacenamiento y picking de productos |
| 4 | **Almacenista** | Operativo | Picking y optimización de operaciones |
| 5 | **Conteo** | Operativo | Conteo físico y validación de existencias |
| 6 | **Control Calidad** | Operativo | Inspección y validación de productos |
| 7 | **Logística** | Operativo | Asignación y gestión de traslados |
| 8 | **Recepción** | Operativo | Recepción en destino de traslados |
| 9 | **Facturación** | Operativo | Registro y gestión de facturas |
| 10 | **Revisión** | Operativo | Revisión y autorización de citas y pedidos |

---

## Matriz de Permisos

### Módulos del Sistema

| Módulo | Descripción | Roles con Acceso |
|--------|-------------|-----------------|
| **Dashboard** | Panel principal | Todos (login_required) |
| **Gestión Logística** | Citas, traslados, conteo | Todos (login_required) |
| **Picking** | Optimización de picking | Administrador, Almacenista, Gestor de Inventario |
| **Reportes** | Análisis y reportes | Administrador, Gestor de Inventario, Analista |
| **Administración** | Gestión de usuarios y roles | Administrador |
| **Entrada/Salida** | Movimientos de inventario | Almacenero, Supervisión, Control Calidad |

---

## Descripción Detallada de Cada Rol

### 1. 👨‍💼 Administrador

**Descripción**: Administrador del sistema con acceso total.

**Responsabilidades**:
- Gestión de usuarios y asignación de roles
- Configuración del sistema
- Creación y eliminación de roles
- Gestión de opciones de menú por rol
- Acceso a todos los reportes y análisis

**Vistas Accesibles**:
- ✅ Dashboard administrativo
- ✅ Gestión de usuarios (crear, editar, eliminar)
- ✅ Gestión de roles (crear, editar, eliminar)
- ✅ Configuración de menú por rol
- ✅ Reportes de acceso y estadísticas
- ✅ Análisis de distribuciones
- ✅ Análisis temporal
- ✅ Reporte general de salidas
- ✅ Dashboard de picking
- ✅ Picking propuestas
- ✅ Panel de administración Django

**Rutas URL**:
```
/admin/                          # Panel de administración Django
/logistica/                      # Todas las vistas de logística
/gestion-inventario/             # Todas las vistas de inventario
/reportes/                       # Todos los reportes
```

**Permisos Especiales**: Acceso total sin restricciones

---

### 2. 📊 Gestor de Inventario

**Descripción**: Responsable de la gestión general del inventario y análisis de datos.

**Responsabilidades**:
- Análisis de inventario y movimientos
- Generación de reportes
- Optimización de picking
- Supervisión de operaciones
- Análisis de distribuciones y tendencias

**Vistas Accesibles**:
- ✅ Dashboard principal
- ✅ Análisis de distribuciones
- ✅ Análisis temporal
- ✅ Reporte general de salidas
- ✅ Dashboard de picking
- ✅ Picking propuestas
- ✅ Gestión logística (citas, traslados, conteo)

**Rutas URL**:
```
/logistica/                      # Todas las vistas de logística
/gestion-inventario/             # Todas las vistas de inventario
/reportes/salidas/               # Reportes de salidas
```

**Permisos Especiales**: Acceso a reportes y análisis avanzados

---

### 3. 🏭 Almacenero

**Descripción**: Responsable de recepción, almacenamiento y picking de productos.

**Responsabilidades**:
- Recepción de productos
- Almacenamiento en ubicaciones
- Picking de pedidos
- Validación de entrada/salida
- Registro de movimientos

**Vistas Accesibles**:
- ✅ Dashboard principal
- ✅ Entrada de almacén (paso 1)
- ✅ Gestión logística (citas, traslados, conteo)
- ✅ Picking (si tiene rol Almacenista)

**Rutas URL**:
```
/logistica/                      # Gestión logística
/inventario/                     # Movimientos de inventario
```

**Permisos Especiales**: Acceso a entrada/salida de almacén

---

### 4. 📦 Almacenista

**Descripción**: Especializado en optimización de picking y operaciones.

**Responsabilidades**:
- Picking de propuestas de pedido
- Optimización de rutas de picking
- Validación de items recogidos
- Generación de movimientos automáticos

**Vistas Accesibles**:
- ✅ Dashboard principal
- ✅ Dashboard de picking
- ✅ Picking propuestas
- ✅ Gestión logística (citas, traslados, conteo)

**Rutas URL**:
```
/picking/                        # Módulo de picking
/logistica/                      # Gestión logística
```

**Permisos Especiales**: Acceso especializado a picking

---

### 5. 📝 Conteo

**Descripción**: Responsable de conteo físico y validación de existencias.

**Responsabilidades**:
- Conteo físico de productos
- Captura de tres conteos (validación IMSS-Bienestar)
- Generación de movimientos por diferencias
- Registro de observaciones

**Vistas Accesibles**:
- ✅ Dashboard principal
- ✅ Búsqueda de lotes para conteo
- ✅ Captura de conteos
- ✅ Historial de conteos
- ✅ Gestión logística (citas, traslados)

**Rutas URL**:
```
/logistica/conteos/              # Todas las vistas de conteo
/logistica/                      # Gestión logística general
```

**Permisos Especiales**: Acceso completo a conteo físico

---

### 6. ✅ Control Calidad

**Descripción**: Responsable de inspección y validación de productos.

**Responsabilidades**:
- Inspección de productos recibidos
- Validación de calidad
- Registro de defectos o anomalías
- Aprobación/rechazo de lotes

**Vistas Accesibles**:
- ✅ Dashboard principal
- ✅ Entrada de almacén (paso 1)
- ✅ Gestión logística (citas, traslados, conteo)

**Rutas URL**:
```
/logistica/                      # Gestión logística
/inventario/                     # Movimientos de inventario
```

**Permisos Especiales**: Acceso a validación de entrada

---

### 7. 🚚 Logística

**Descripción**: Responsable de asignación y gestión de traslados.

**Responsabilidades**:
- Asignación de traslados
- Gestión de rutas
- Seguimiento de envíos
- Coordinación con recepción

**Vistas Accesibles**:
- ✅ Dashboard principal
- ✅ Gestión logística completa:
  - Citas de proveedores
  - Traslados
  - Conteo físico
  - Pedidos
  - Llegadas de proveedores

**Rutas URL**:
```
/logistica/                      # Todas las vistas de logística
```

**Permisos Especiales**: Acceso completo a logística

---

### 8. 📥 Recepción

**Descripción**: Responsable de recepción en destino de traslados.

**Responsabilidades**:
- Recepción de traslados
- Confirmación de llegada
- Validación de cantidades
- Registro de recepción

**Vistas Accesibles**:
- ✅ Dashboard principal
- ✅ Gestión logística:
  - Traslados (confirmación de recepción)
  - Conteo físico
  - Llegadas de proveedores

**Rutas URL**:
```
/logistica/                      # Gestión logística
```

**Permisos Especiales**: Acceso a confirmación de recepción

---

### 9. 💰 Facturación

**Descripción**: Responsable de registro y gestión de facturas.

**Responsabilidades**:
- Registro de facturas
- Validación de montos
- Reconciliación con pedidos
- Generación de reportes de facturación

**Vistas Accesibles**:
- ✅ Dashboard principal
- ✅ Gestión logística (citas, traslados, conteo)

**Rutas URL**:
```
/logistica/                      # Gestión logística
```

**Permisos Especiales**: Acceso a facturación (cuando esté implementado)

---

### 10. 🔍 Revisión

**Descripción**: Responsable de revisión y autorización de citas y pedidos.

**Responsabilidades**:
- Revisión de citas de proveedores
- Autorización de pedidos
- Validación de solicitudes
- Aprobación de cambios

**Vistas Accesibles**:
- ✅ Dashboard principal
- ✅ Gestión logística:
  - Citas (revisión y autorización)
  - Pedidos (validación)
  - Traslados
  - Conteo

**Rutas URL**:
```
/logistica/                      # Gestión logística
```

**Permisos Especiales**: Acceso a autorización de citas

---

## Flujos de Trabajo por Rol

### 📋 Flujo de Recepción de Productos

```
Revisión (Autoriza cita)
    ↓
Almacenero (Recibe productos)
    ↓
Control Calidad (Inspecciona)
    ↓
Almacenero (Almacena en ubicación)
    ↓
Gestor de Inventario (Valida en sistema)
```

### 📦 Flujo de Picking

```
Gestor de Inventario (Crea propuesta)
    ↓
Almacenista (Realiza picking)
    ↓
Almacenista (Marca items recogidos)
    ↓
Sistema (Genera movimientos automáticamente)
```

### 🚚 Flujo de Traslado

```
Logística (Crea traslado)
    ↓
Logística (Asigna logística)
    ↓
Logística (Inicia tránsito)
    ↓
Recepción (Confirma recepción)
    ↓
Logística (Completa traslado)
```

### 📝 Flujo de Conteo Físico

```
Conteo (Busca lote)
    ↓
Conteo (Captura primer conteo)
    ↓
Conteo (Captura segundo conteo)
    ↓
Conteo (Captura tercer conteo - DEFINITIVO)
    ↓
Sistema (Genera movimiento de diferencia)
```

---

## Pruebas de Acceso

### Cómo Probar Manualmente

1. **Crear usuario de prueba**:
   ```bash
   docker-compose exec web python manage.py shell
   ```
   
   ```python
   from django.contrib.auth.models import User, Group
   
   # Crear usuario
   usuario = User.objects.create_user(
       username='prueba_almacenero',
       password='prueba123',
       email='prueba@test.com'
   )
   
   # Asignar rol
   grupo = Group.objects.get(name='Almacenero')
   usuario.groups.add(grupo)
   ```

2. **Iniciar sesión** con el usuario de prueba
3. **Verificar acceso** a las vistas permitidas
4. **Intentar acceso** a vistas no permitidas (debería mostrar error)

### Pruebas Automáticas

Ejecutar el script de pruebas:
```bash
docker-compose exec web python manage.py test_roles_acceso
```

---

## Matriz de Acceso Rápida

| Funcionalidad | Admin | Gestor | Almacenero | Almacenista | Conteo | Control | Logística | Recepción | Facturación | Revisión |
|---------------|:-----:|:------:|:----------:|:-----------:|:------:|:-------:|:---------:|:---------:|:-----------:|:--------:|
| Dashboard | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Citas | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Traslados | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Conteo Físico | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Picking | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Entrada/Salida | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Reportes | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Admin Roles | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |

---

## Notas Importantes

### 🔒 Seguridad

- Los roles se validan en **cada petición** (no se cachean)
- Los superusuarios (`is_superuser=True`) tienen acceso a todo
- Los cambios de roles se aplican **inmediatamente** sin reiniciar
- Todos los accesos se pueden auditar a través de logs

### 🔄 Cambios de Roles

Para cambiar los roles de un usuario:

```bash
docker-compose exec web python manage.py shell
```

```python
from django.contrib.auth.models import User, Group

usuario = User.objects.get(username='nombre_usuario')

# Ver roles actuales
print(usuario.groups.all())

# Agregar rol
grupo = Group.objects.get(name='Nuevo Rol')
usuario.groups.add(grupo)

# Remover rol
usuario.groups.remove(grupo)

# Reemplazar todos los roles
usuario.groups.set([Group.objects.get(name='Rol 1'), Group.objects.get(name='Rol 2')])
```

### 📊 Monitoreo

Para ver qué usuarios tienen cada rol:

```python
from django.contrib.auth.models import Group

grupo = Group.objects.get(name='Almacenero')
usuarios = grupo.user_set.all()

for usuario in usuarios:
    print(f"{usuario.username}: {usuario.email}")
```

---

## Troubleshooting

### "No tienes permiso para acceder a esta sección"

**Causas**:
- El usuario no tiene el rol requerido
- El usuario tiene un rol diferente al esperado
- La sesión no se ha actualizado

**Soluciones**:
1. Verificar que el usuario tiene el rol correcto:
   ```bash
   docker-compose exec web python manage.py shell
   ```
   ```python
   from django.contrib.auth.models import User
   usuario = User.objects.get(username='nombre')
   print(usuario.groups.all())
   ```

2. Cerrar sesión y volver a iniciar
3. Limpiar caché del navegador (Ctrl+Shift+Del)

### Un rol no aparece en el sistema

1. Verificar que el rol existe:
   ```bash
   docker-compose exec web python manage.py shell
   ```
   ```python
   from django.contrib.auth.models import Group
   print(Group.objects.all())
   ```

2. Si no existe, crear los roles:
   ```bash
   docker-compose exec web python manage.py crear_roles
   ```

---

## Contacto y Soporte

Para reportar problemas con roles o acceso:
1. Verificar este manual
2. Revisar los logs del servidor
3. Contactar al administrador del sistema

---

**Documento generado**: Diciembre 2025  
**Versión del Sistema**: 1.0  
**Estado**: Producción
