# 📋 Análisis Completo del Menú - Asignación de Roles

## Resumen Ejecutivo

Se ha identificado que el menú en `base.html` tiene **14 opciones principales** que necesitan control de acceso basado en roles. Actualmente, solo **5 opciones** tienen template tags configurados. Se necesita agregar template tags a las **9 opciones restantes**.

---

## 📊 Opciones del Menú - Estado Actual

### ✅ CON TEMPLATE TAGS (5 opciones)

| Opción | Roles Permitidos | Template Tag |
|--------|-----------------|--------------|
| **Dashboard** | Todos | ✅ Sin restricción |
| **Instituciones** | Administrador | ✅ `usuario_tiene_rol:"Administrador"` |
| **Productos** | Administrador | ✅ `usuario_tiene_rol:"Administrador"` |
| **Existencias** | Almacenero, Supervisión, Control Calidad, Facturación, Gestor | ✅ `usuario_tiene_alguno_de_estos_roles` |
| **Operaciones** | Almacenero, Supervisión, Control Calidad | ✅ `usuario_tiene_alguno_de_estos_roles` |

### ❌ SIN TEMPLATE TAGS (9 opciones)

| Opción | Ubicación | Roles Sugeridos | Acción |
|--------|-----------|-----------------|--------|
| **Gestión Logística** | Línea 218 | Revisión, Supervisión, Logística, Recepción, Conteo | ❌ Agregar |
| **Inventario** | Línea 315 | Supervisión, Gestor de Inventario | ❌ Agregar |
| **Alertas** | Línea 322 | Supervisión, Gestor de Inventario | ❌ Agregar |
| **Solicitudes** | Línea 330 | Revisión, Supervisión | ❌ Agregar |
| **Cargas Masivas** | Línea 357 | Administrador, Almacenero | ❌ Agregar |
| **Picking y Operaciones** | Línea 384 | Almacenero, Supervisión | ❌ Agregar |
| **Administración de Roles** | Línea 404 | Administrador | ⚠️ Sintaxis incorrecta |
| **Panel de Django** | Línea 414 | Administrador | ❌ Agregar |
| **Cerrar Sesión** | Línea 421 | Todos | ✅ Sin restricción |

---

## 🎯 Detalles de Opciones sin Template Tags

### 1. **Gestión Logística** (Línea 218)

**Subopciones:**
- Citas de Proveedores → Revisión, Supervisión
- Traslados → Logística, Supervisión
- Conteo Físico → Conteo, Supervisión
- Gestión de Pedidos → Revisión, Supervisión, Logística
- Propuestas de Surtimiento → Almacenero, Supervisión
- Llegada de Proveedores → Recepción, Supervisión
- Devoluciones de Proveedores → Supervisión, Logística
- Reportes de Devoluciones → Supervisión, Administrador
- Reportes de Salidas → Supervisión, Administrador

**Recomendación:**
```django
{% if user|usuario_tiene_alguno_de_estos_roles:"Revisión,Supervisión,Logística,Recepción,Conteo,Almacenero" %}
    <!-- Mostrar Gestión Logística -->
{% endif %}
```

### 2. **Inventario** (Línea 315)

**Descripción:** Movimientos de inventario

**Roles Sugeridos:** Supervisión, Gestor de Inventario, Administrador

**Recomendación:**
```django
{% if user|usuario_tiene_alguno_de_estos_roles:"Supervisión,Gestor de Inventario" %}
    <!-- Mostrar Inventario -->
{% endif %}
```

### 3. **Alertas** (Línea 322)

**Descripción:** Alertas de caducidad

**Roles Sugeridos:** Supervisión, Gestor de Inventario, Administrador

**Recomendación:**
```django
{% if user|usuario_tiene_alguno_de_estos_roles:"Supervisión,Gestor de Inventario" %}
    <!-- Mostrar Alertas -->
{% endif %}
```

### 4. **Solicitudes** (Línea 330)

**Subopciones:**
- Lista de solicitudes → Revisión, Supervisión
- Carga masiva → Administrador, Almacenero
- Complemento de carga → Administrador, Almacenero

**Recomendación:**
```django
{% if user|usuario_tiene_alguno_de_estos_roles:"Revisión,Supervisión,Administrador,Almacenero" %}
    <!-- Mostrar Solicitudes -->
{% endif %}
```

### 5. **Cargas Masivas** (Línea 357)

**Subopciones:**
- Instituciones → Administrador
- Existencias → Almacenero, Supervisión
- Solicitudes → Administrador, Almacenero

**Recomendación:**
```django
{% if user|usuario_tiene_alguno_de_estos_roles:"Administrador,Almacenero,Supervisión" %}
    <!-- Mostrar Cargas Masivas -->
{% endif %}
```

### 6. **Picking y Operaciones** (Línea 384)

**Subopciones:**
- Propuestas para Picking → Almacenero, Supervisión

**Recomendación:**
```django
{% if user|usuario_tiene_alguno_de_estos_roles:"Almacenero,Supervisión" %}
    <!-- Mostrar Picking y Operaciones -->
{% endif %}
```

### 7. **Administración de Roles** (Línea 404)

**Problema Actual:**
```django
{% if user.is_superuser or 'Administrador' in user.groups.values_list.name %}
```

**Sintaxis Incorrecta:** `values_list.name` no es válido

**Recomendación:**
```django
{% if user|usuario_tiene_rol:"Administrador" %}
    <!-- Mostrar Administración de Roles -->
{% endif %}
```

### 8. **Panel de Django** (Línea 414)

**Descripción:** Acceso a Django Admin

**Roles Sugeridos:** Administrador

**Recomendación:**
```django
{% if user|usuario_tiene_rol:"Administrador" %}
    <!-- Mostrar Panel de Django -->
{% endif %}
```

---

## 📈 Matriz de Acceso Completa

| Opción | Admin | Revisión | Almacenero | Supervisión | Control Calidad | Facturación | Logística | Recepción | Conteo | Gestor |
|--------|-------|----------|-----------|-------------|-----------------|------------|-----------|-----------|--------|--------|
| Dashboard | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Instituciones | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Productos | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Existencias | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ |
| Operaciones | ✅ | ❌ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Gestión Logística | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ | ✅ | ✅ | ❌ |
| Inventario | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Alertas | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Solicitudes | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Cargas Masivas | ✅ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Picking | ✅ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Admin Roles | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Panel Django | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |

---

## 🔧 Plan de Acción

### Paso 1: Corregir Sintaxis (Línea 404)
Cambiar:
```django
{% if user.is_superuser or 'Administrador' in user.groups.values_list.name %}
```

Por:
```django
{% if user|usuario_tiene_rol:"Administrador" %}
```

### Paso 2: Agregar Template Tags a Gestión Logística

Envolver la sección completa (líneas 218-313) con:
```django
{% if user|usuario_tiene_alguno_de_estos_roles:"Revisión,Supervisión,Logística,Recepción,Conteo,Almacenero" %}
    <!-- Gestión Logística -->
{% endif %}
```

Luego, agregar condicionales a cada subopciones:
- **Citas de Proveedores** → `usuario_tiene_alguno_de_estos_roles:"Revisión,Supervisión"`
- **Traslados** → `usuario_tiene_alguno_de_estos_roles:"Logística,Supervisión"`
- **Conteo Físico** → `usuario_tiene_alguno_de_estos_roles:"Conteo,Supervisión"`
- **Gestión de Pedidos** → `usuario_tiene_alguno_de_estos_roles:"Revisión,Supervisión,Logística"`
- **Propuestas de Surtimiento** → `usuario_tiene_alguno_de_estos_roles:"Almacenero,Supervisión"`
- **Llegada de Proveedores** → `usuario_tiene_alguno_de_estos_roles:"Recepción,Supervisión"`
- **Devoluciones** → `usuario_tiene_alguno_de_estos_roles:"Supervisión,Logística"`
- **Reportes** → `usuario_tiene_alguno_de_estos_roles:"Supervisión"`

### Paso 3: Agregar Template Tags a Opciones Restantes

Aplicar template tags a:
- Inventario (línea 315)
- Alertas (línea 322)
- Solicitudes (línea 330)
- Cargas Masivas (línea 357)
- Picking y Operaciones (línea 384)
- Panel de Django (línea 414)

### Paso 4: Validación

Probar con cada rol para verificar que:
1. ✅ Solo ve las opciones permitidas
2. ✅ Las subopciones se filtran correctamente
3. ✅ No hay errores de sintaxis
4. ✅ El menú se colapsa/expande correctamente

---

## 📝 Notas Importantes

1. **Gestión Logística** es la sección más compleja con 9 subopciones que necesitan filtrado individual
2. **Reportes** (Devoluciones y Salidas) deben estar disponibles solo para Supervisión y Administrador
3. **Cargas Masivas** tiene subopciones con diferentes roles, necesita filtrado granular
4. **Panel de Django** debería estar restringido a Administrador solamente
5. El menú debe colapsar/expandirse correctamente cuando se ocultan todas las subopciones

---

**Estado:** 📋 Análisis Completado  
**Próximo Paso:** Implementar template tags en todas las opciones  
**Estimado:** 2-3 commits
