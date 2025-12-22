# Agregar Menús Bajo Demanda

## Descripción

Ahora puedes agregar nuevos menús y submenús directamente desde Django Admin **sin necesidad de modificar código**.

El campo **"Opción de Menú"** es completamente flexible y acepta cualquier identificador único.

## Formas de Agregar Menús

### **Opción 1: Django Admin (Recomendado - Más Fácil)**

La forma más sencilla es usar la interfaz de Django Admin:

1. **Ir a**: `http://tu-servidor/admin/`
2. **Navegar a**: Inventario → Menu Item Rol
3. **Click en "Agregar Menu Item Rol"**
4. **Llenar los campos**:
   - **Opción de Menú**: `gestion_proveedores` (identificador único, sin espacios)
   - **Nombre Mostrado**: `Gestión de Proveedores` (lo que ve el usuario)
   - **Icono Font Awesome**: `fas fa-truck` (ej: [Font Awesome Icons](https://fontawesome.com/icons))
   - **Nombre de URL**: `gestion_proveedores` (debe existir en urls.py)
   - **Menú Padre**: Dejar vacío para menú raíz
   - **Orden**: `10` (número para ordenar)
   - **Activo**: ✓ (marcar para que sea visible)
   - **Roles Permitidos**: Seleccionar los roles que pueden ver este menú
5. **Click en "Guardar"**

---

### **Opción 2: Django Shell (Rápido)**

Para crear menús desde la línea de comandos:

```bash
docker-compose exec web python manage.py shell
```

**Crear un menú raíz:**

```python
from inventario.models import MenuItemRol

# Crear menú raíz
MenuItemRol.crear_menu_raiz(
    menu_item='gestion_proveedores',
    nombre_mostrado='Gestión de Proveedores',
    icono='fas fa-truck',
    url_name='gestion_proveedores',
    orden=10
)
```

**Crear un submenú:**

```python
# Obtener el menú padre
padre = MenuItemRol.objects.get(nombre_mostrado='Gestión de Proveedores')

# Crear submenú
MenuItemRol.crear_submenu(
    menu_item='lista_proveedores',
    nombre_mostrado='Listar Proveedores',
    menu_padre=padre,
    icono='fas fa-list',
    url_name='lista_proveedores',
    orden=1
)
```

**Asignar roles:**

```python
from django.contrib.auth.models import Group

# Obtener el menú
menu = MenuItemRol.objects.get(menu_item='gestion_proveedores')

# Obtener el grupo (rol)
admin_group = Group.objects.get(name='Administrador')

# Asignar el rol
menu.roles_permitidos.add(admin_group)
```

---

### **Opción 3: Script Python Personalizado (Avanzado)**

Crear un script para agregar múltiples menús de una vez:

```bash
# Crear archivo
cat > agregar_menus_personalizados.py << 'EOF'
from inventario.models import MenuItemRol
from django.contrib.auth.models import Group

# Obtener roles
admin = Group.objects.get(name='Administrador')
almacenero = Group.objects.get(name='Almacenero')

# Crear menú raíz
gestion_prov = MenuItemRol.crear_menu_raiz(
    menu_item='gestion_proveedores',
    nombre_mostrado='Gestión de Proveedores',
    icono='fas fa-truck',
    url_name='gestion_proveedores',
    orden=15
)
gestion_prov.roles_permitidos.add(admin, almacenero)

# Crear submenús
submenus = [
    ('lista_proveedores', 'Listar Proveedores', 'fas fa-list'),
    ('crear_proveedor', 'Crear Proveedor', 'fas fa-plus'),
    ('editar_proveedor', 'Editar Proveedor', 'fas fa-edit'),
    ('eliminar_proveedor', 'Eliminar Proveedor', 'fas fa-trash'),
]

for menu_item, nombre, icono in submenus:
    submenu = MenuItemRol.crear_submenu(
        menu_item=menu_item,
        nombre_mostrado=nombre,
        menu_padre=gestion_prov,
        icono=icono,
        url_name=menu_item
    )
    submenu.roles_permitidos.add(admin, almacenero)

print("✅ Menús agregados correctamente")
EOF

# Ejecutar
docker-compose exec web python manage.py shell < agregar_menus_personalizados.py
```

---

## Estructura de Ejemplo

Después de agregar menús, tu estructura podría verse así:

```
Dashboard (raíz)
├── Instituciones (raíz)
├── Productos (raíz)
├── Administración (padre)
│   ├── Usuarios (submenu)
│   ├── Roles (submenu)
│   └── Opciones de Menú (submenu)
├── Gestión de Proveedores (padre) ← NUEVO
│   ├── Listar Proveedores (submenu)
│   ├── Crear Proveedor (submenu)
│   ├── Editar Proveedor (submenu)
│   └── Eliminar Proveedor (submenu)
└── Reportes (padre)
    ├── Reporte General (submenu)
    └── Análisis (submenu)
```

---

## Validación Automática

El modelo valida automáticamente:

✅ **Identificadores únicos**
- No permite dos menús con el mismo `menu_item`

✅ **Referencias circulares**
- No permite que un menú sea su propio padre
- No permite cadenas circulares (A → B → A)

✅ **Campos obligatorios**
- `menu_item` no puede estar vacío
- `nombre_mostrado` es obligatorio

---

## Métodos Disponibles

### `MenuItemRol.crear_menu_raiz()`

Crea un menú raíz (sin padre):

```python
MenuItemRol.crear_menu_raiz(
    menu_item='gestion_proveedores',      # Identificador único
    nombre_mostrado='Gestión de Proveedores',  # Nombre visible
    icono='fas fa-truck',                 # Icono Font Awesome
    url_name='gestion_proveedores',       # Nombre de URL
    orden=10                              # Orden de aparición
)
```

### `MenuItemRol.crear_submenu()`

Crea un submenú bajo un padre:

```python
padre = MenuItemRol.objects.get(nombre_mostrado='Gestión de Proveedores')

MenuItemRol.crear_submenu(
    menu_item='lista_proveedores',
    nombre_mostrado='Listar Proveedores',
    menu_padre=padre,
    icono='fas fa-list',
    url_name='lista_proveedores',
    orden=1
)
```

---

## Iconos Font Awesome Recomendados

| Categoría | Icono | Código |
|-----------|-------|--------|
| **Administración** | ⚙️ | `fas fa-cog` |
| **Usuarios** | 👥 | `fas fa-users` |
| **Roles** | 🔐 | `fas fa-lock` |
| **Productos** | 📦 | `fas fa-box` |
| **Proveedores** | 🚚 | `fas fa-truck` |
| **Reportes** | 📊 | `fas fa-chart-bar` |
| **Configuración** | ⚙️ | `fas fa-sliders-h` |
| **Documentos** | 📄 | `fas fa-file` |
| **Historial** | 📜 | `fas fa-history` |
| **Buscar** | 🔍 | `fas fa-search` |
| **Editar** | ✏️ | `fas fa-edit` |
| **Eliminar** | 🗑️ | `fas fa-trash` |
| **Agregar** | ➕ | `fas fa-plus` |
| **Listar** | 📋 | `fas fa-list` |

Ver más en: [Font Awesome Icons](https://fontawesome.com/icons)

---

## Troubleshooting

### Error: "Ya existe un menú con el identificador..."

**Causa**: El `menu_item` ya existe

**Solución**: Usa un identificador diferente, ej: `gestion_proveedores_v2`

### El menú no aparece en el navegador

**Causa**: El usuario no tiene el rol asignado

**Solución**:
1. Ir a Django Admin → Usuarios
2. Editar el usuario
3. Asignar los grupos (roles) necesarios

### El icono no se ve

**Causa**: El código de Font Awesome es incorrecto

**Solución**:
1. Verificar en [Font Awesome Icons](https://fontawesome.com/icons)
2. Usar el formato correcto: `fas fa-nombre`

---

## Mejores Prácticas

✅ **DO's**
- Usar identificadores descriptivos en minúsculas
- Agrupar items relacionados bajo el mismo padre
- Usar iconos consistentes
- Mantener el orden lógico
- Asignar roles apropiados

❌ **DON'Ts**
- No usar espacios en `menu_item`
- No crear más de 3 niveles de profundidad
- No mezclar categorías diferentes
- No usar nombres muy largos
- No olvidar asignar roles

---

## Próximos Pasos

1. ✅ Agregar tus menús personalizados desde Django Admin
2. ✅ Asignar roles a cada menú
3. ✅ Probar con diferentes usuarios
4. ✅ Ajustar iconos y orden según sea necesario
5. ✅ Documentar tu estructura de menús
