# 🧪 Plan de Pruebas - Sistema de Gestión de Roles

## Objetivo

Verificar que el sistema de gestión de roles funciona correctamente y que cada usuario solo ve las funcionalidades asignadas según su rol.

---

## Usuarios de Prueba

| Usuario | Rol | Contraseña | Email |
|---------|-----|-----------|-------|
| revision1 | Revisión | revision123 | revision@almacen.local |
| almacenero1 | Almacenero | almacen123 | almacenero1@almacen.local |
| almacenero2 | Almacenero | almacen123 | almacenero2@almacen.local |
| calidad1 | Control Calidad | calidad123 | calidad@almacen.local |
| facturacion1 | Facturación | factura123 | facturacion@almacen.local |
| supervision1 | Supervisión | supervision123 | supervision@almacen.local |
| logistica1 | Logística | logistica123 | logistica@almacen.local |
| recepcion1 | Recepción | recepcion123 | recepcion@almacen.local |
| conteo1 | Conteo | conteo123 | conteo@almacen.local |
| gestor1 | Gestor de Inventario | gestor123 | gestor@almacen.local |

---

## Pruebas por Rol

### 1️⃣ **ADMINISTRADOR**

**Usuario:** admin (contraseña: tu-contraseña)

**Opciones de Menú Esperadas:**
- ✅ Dashboard
- ✅ Administración de Roles
- ✅ Instituciones
- ✅ Productos
- ✅ Proveedores
- ✅ Alcaldías
- ✅ Almacenes
- ✅ Existencias
- ✅ Operaciones
- ✅ Gestión Logística
- ✅ Inventario
- ✅ Alertas
- ✅ Solicitudes
- ✅ Cargas Masivas
- ✅ Picking y Operaciones
- ✅ Panel de Django

**Pruebas a Realizar:**

1. **Acceso al Dashboard de Roles**
   ```
   URL: http://tu-servidor/admin-roles/
   Resultado esperado: ✅ Acceso permitido
   ```

2. **Gestión de Usuarios**
   ```
   URL: http://tu-servidor/admin-roles/usuarios/
   Resultado esperado: ✅ Acceso permitido
   ```

3. **Gestión de Roles**
   ```
   URL: http://tu-servidor/admin-roles/roles/
   Resultado esperado: ✅ Acceso permitido
   ```

4. **Configuración de Menú**
   ```
   URL: http://tu-servidor/admin-roles/menu/
   Resultado esperado: ✅ Acceso permitido
   ```

5. **Reportes**
   ```
   URL: http://tu-servidor/admin-roles/reporte-acceso/
   Resultado esperado: ✅ Acceso permitido
   ```

---

### 2️⃣ **ALMACENERO**

**Usuario:** almacenero1
**Contraseña:** almacen123

**Opciones de Menú Esperadas:**
- ✅ Dashboard
- ✅ Existencias
- ✅ Operaciones (Entrada, Salidas)
- ✅ Gestión Logística (Picking)
- ✅ Inventario
- ✅ Alertas

**Opciones NO Esperadas:**
- ❌ Administración de Roles
- ❌ Instituciones
- ❌ Productos
- ❌ Proveedores
- ❌ Panel de Django

**Pruebas a Realizar:**

1. **Acceso a Picking**
   ```
   URL: http://tu-servidor/picking/
   Resultado esperado: ✅ Acceso permitido
   ```

2. **Acceso a Entrada al Almacén**
   ```
   URL: http://tu-servidor/entrada_almacen/paso1/
   Resultado esperado: ✅ Acceso permitido
   ```

3. **Intento de Acceso a Administración de Roles**
   ```
   URL: http://tu-servidor/admin-roles/
   Resultado esperado: ❌ Acceso denegado (403 o redirección)
   ```

4. **Intento de Acceso a Instituciones**
   ```
   URL: http://tu-servidor/instituciones/
   Resultado esperado: ❌ Acceso denegado
   ```

5. **Verificar que NO ve opción en menú**
   ```
   Resultado esperado: ❌ No aparece "Administración de Roles"
   Resultado esperado: ❌ No aparece "Instituciones"
   ```

---

### 3️⃣ **SUPERVISIÓN**

**Usuario:** supervision1
**Contraseña:** supervision123

**Opciones de Menú Esperadas:**
- ✅ Dashboard
- ✅ Existencias
- ✅ Operaciones
- ✅ Gestión Logística (Ver todo)
- ✅ Inventario
- ✅ Alertas
- ✅ Solicitudes
- ✅ Reportes

**Opciones NO Esperadas:**
- ❌ Administración de Roles
- ❌ Instituciones
- ❌ Productos
- ❌ Panel de Django

**Pruebas a Realizar:**

1. **Acceso a Reportes**
   ```
   URL: http://tu-servidor/reportes_devoluciones/reporte_general/
   Resultado esperado: ✅ Acceso permitido
   ```

2. **Acceso a Gestión Logística**
   ```
   URL: http://tu-servidor/logistica/pedidos/
   Resultado esperado: ✅ Acceso permitido
   ```

3. **Intento de Acceso a Administración**
   ```
   URL: http://tu-servidor/admin-roles/
   Resultado esperado: ❌ Acceso denegado
   ```

4. **Verificar Menú**
   ```
   Resultado esperado: ✅ Ve "Reportes"
   Resultado esperado: ❌ No ve "Administración de Roles"
   ```

---

### 4️⃣ **CONTROL CALIDAD**

**Usuario:** calidad1
**Contraseña:** calidad123

**Opciones de Menú Esperadas:**
- ✅ Dashboard
- ✅ Existencias
- ✅ Operaciones (Entrada)
- ✅ Alertas

**Opciones NO Esperadas:**
- ❌ Administración de Roles
- ❌ Gestión Logística
- ❌ Reportes
- ❌ Panel de Django

**Pruebas a Realizar:**

1. **Acceso a Entrada al Almacén**
   ```
   URL: http://tu-servidor/entrada_almacen/paso1/
   Resultado esperado: ✅ Acceso permitido
   ```

2. **Intento de Acceso a Picking**
   ```
   URL: http://tu-servidor/picking/
   Resultado esperado: ❌ Acceso denegado
   ```

3. **Intento de Acceso a Reportes**
   ```
   URL: http://tu-servidor/reportes_devoluciones/
   Resultado esperado: ❌ Acceso denegado
   ```

---

### 5️⃣ **FACTURACIÓN**

**Usuario:** facturacion1
**Contraseña:** factura123

**Opciones de Menú Esperadas:**
- ✅ Dashboard
- ✅ Existencias (Ver)
- ✅ Alertas

**Opciones NO Esperadas:**
- ❌ Administración de Roles
- ❌ Operaciones
- ❌ Picking
- ❌ Panel de Django

**Pruebas a Realizar:**

1. **Acceso a Lista de Existencias**
   ```
   URL: http://tu-servidor/lotes/
   Resultado esperado: ✅ Acceso permitido (solo lectura)
   ```

2. **Intento de Acceso a Entrada al Almacén**
   ```
   URL: http://tu-servidor/entrada_almacen/paso1/
   Resultado esperado: ❌ Acceso denegado
   ```

---

### 6️⃣ **REVISIÓN**

**Usuario:** revision1
**Contraseña:** revision123

**Opciones de Menú Esperadas:**
- ✅ Dashboard
- ✅ Gestión Logística (Citas, Pedidos)
- ✅ Solicitudes

**Opciones NO Esperadas:**
- ❌ Administración de Roles
- ❌ Operaciones
- ❌ Panel de Django

**Pruebas a Realizar:**

1. **Acceso a Citas**
   ```
   URL: http://tu-servidor/logistica/citas/
   Resultado esperado: ✅ Acceso permitido
   ```

2. **Acceso a Solicitudes**
   ```
   URL: http://tu-servidor/solicitudes/
   Resultado esperado: ✅ Acceso permitido
   ```

3. **Intento de Acceso a Picking**
   ```
   URL: http://tu-servidor/picking/
   Resultado esperado: ❌ Acceso denegado
   ```

---

### 7️⃣ **LOGÍSTICA**

**Usuario:** logistica1
**Contraseña:** logistica123

**Opciones de Menú Esperadas:**
- ✅ Dashboard
- ✅ Gestión Logística (Traslados, Pedidos)
- ✅ Existencias (Ver)

**Opciones NO Esperadas:**
- ❌ Administración de Roles
- ❌ Operaciones
- ❌ Panel de Django

**Pruebas a Realizar:**

1. **Acceso a Traslados**
   ```
   URL: http://tu-servidor/logistica/traslados/
   Resultado esperado: ✅ Acceso permitido
   ```

2. **Intento de Acceso a Picking**
   ```
   URL: http://tu-servidor/picking/
   Resultado esperado: ❌ Acceso denegado
   ```

---

### 8️⃣ **RECEPCIÓN**

**Usuario:** recepcion1
**Contraseña:** recepcion123

**Opciones de Menú Esperadas:**
- ✅ Dashboard
- ✅ Existencias
- ✅ Gestión Logística (Llegada de Proveedores)

**Opciones NO Esperadas:**
- ❌ Administración de Roles
- ❌ Operaciones
- ❌ Panel de Django

**Pruebas a Realizar:**

1. **Acceso a Llegada de Proveedores**
   ```
   URL: http://tu-servidor/logistica/llegadas/
   Resultado esperado: ✅ Acceso permitido
   ```

2. **Intento de Acceso a Entrada al Almacén**
   ```
   URL: http://tu-servidor/entrada_almacen/paso1/
   Resultado esperado: ❌ Acceso denegado
   ```

---

### 9️⃣ **CONTEO**

**Usuario:** conteo1
**Contraseña:** conteo123

**Opciones de Menú Esperadas:**
- ✅ Dashboard
- ✅ Existencias
- ✅ Gestión Logística (Conteo Físico)

**Opciones NO Esperadas:**
- ❌ Administración de Roles
- ❌ Operaciones
- ❌ Panel de Django

**Pruebas a Realizar:**

1. **Acceso a Conteo Físico**
   ```
   URL: http://tu-servidor/logistica/conteo/
   Resultado esperado: ✅ Acceso permitido
   ```

2. **Intento de Acceso a Picking**
   ```
   URL: http://tu-servidor/picking/
   Resultado esperado: ❌ Acceso denegado
   ```

---

### 🔟 **GESTOR DE INVENTARIO**

**Usuario:** gestor1
**Contraseña:** gestor123

**Opciones de Menú Esperadas:**
- ✅ Dashboard
- ✅ Existencias
- ✅ Gestión Logística (Ver todo)
- ✅ Inventario
- ✅ Alertas
- ✅ Solicitudes

**Opciones NO Esperadas:**
- ❌ Administración de Roles
- ❌ Operaciones
- ❌ Panel de Django

**Pruebas a Realizar:**

1. **Acceso a Inventario**
   ```
   URL: http://tu-servidor/movimientos/
   Resultado esperado: ✅ Acceso permitido
   ```

2. **Acceso a Gestión Logística**
   ```
   URL: http://tu-servidor/logistica/pedidos/
   Resultado esperado: ✅ Acceso permitido
   ```

3. **Intento de Acceso a Administración**
   ```
   URL: http://tu-servidor/admin-roles/
   Resultado esperado: ❌ Acceso denegado
   ```

---

## Matriz de Pruebas

| Funcionalidad | Admin | Almacenero | Supervisión | Calidad | Facturación | Revisión | Logística | Recepción | Conteo | Gestor |
|---------------|-------|-----------|-------------|---------|-----------|---------|----------|----------|--------|--------|
| Dashboard | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Admin Roles | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Instituciones | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Productos | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Existencias | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ |
| Entrada Almacén | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Picking | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Citas | ✅ | ❌ | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Traslados | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| Conteo Físico | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| Reportes | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Inventario | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Alertas | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Solicitudes | ✅ | ❌ | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ |

---

## Checklist de Pruebas

### Menú Dinámico
- [ ] Administrador ve todas las opciones
- [ ] Almacenero ve solo operaciones
- [ ] Supervisión ve operaciones y reportes
- [ ] Control Calidad ve solo entrada
- [ ] Facturación ve solo existencias
- [ ] Revisión ve citas y solicitudes
- [ ] Logística ve traslados
- [ ] Recepción ve llegadas
- [ ] Conteo ve conteo físico
- [ ] Gestor ve inventario

### Control de Acceso
- [ ] Almacenero no puede acceder a /admin-roles/
- [ ] Supervisión no puede acceder a /admin-roles/
- [ ] Control Calidad no puede acceder a /picking/
- [ ] Facturación no puede acceder a /entrada_almacen/
- [ ] Revisión no puede acceder a /picking/
- [ ] Logística no puede acceder a /entrada_almacen/
- [ ] Recepción no puede acceder a /picking/
- [ ] Conteo no puede acceder a /picking/
- [ ] Gestor no puede acceder a /admin-roles/

### Opciones de Menú
- [ ] "Administración de Roles" solo aparece para Administrador
- [ ] "Instituciones" solo aparece para Administrador
- [ ] "Productos" solo aparece para Administrador
- [ ] "Panel de Django" solo aparece para Administrador
- [ ] Dashboard aparece para todos

---

## Reporte de Resultados

Después de completar las pruebas, completa este reporte:

### Pruebas Exitosas
- [ ] Menú dinámico funciona correctamente
- [ ] Control de acceso en vistas funciona
- [ ] Cada usuario solo ve sus opciones
- [ ] Acceso denegado funciona correctamente

### Problemas Encontrados
```
Descripción:
Rol Afectado:
URL:
Comportamiento Esperado:
Comportamiento Real:
```

### Notas Adicionales
```
[Espacio para notas]
```

---

## Instrucciones de Ejecución

1. **Accede a tu servidor AWS**
   ```bash
   ssh -i tu-clave.pem ubuntu@tu-servidor
   ```

2. **Asegúrate de tener los datos cargados**
   ```bash
   docker-compose exec web python manage.py crear_roles
   docker-compose exec web python manage.py cargar_menu_roles
   docker-compose exec web python manage.py configurar_permisos_roles
   docker-compose exec web python manage.py cargar_usuarios_ejemplo
   ```

3. **Accede a la aplicación**
   ```
   URL: http://tu-servidor:8700/
   ```

4. **Prueba cada usuario**
   - Inicia sesión con cada usuario
   - Verifica el menú
   - Intenta acceder a URLs restringidas
   - Completa el checklist

5. **Documenta los resultados**
   - Toma capturas de pantalla
   - Anota cualquier problema
   - Completa el reporte

---

**Última actualización**: Diciembre 2025
**Versión**: 1.0
