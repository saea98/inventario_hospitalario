# Sistema de Menús Jerárquicos

## Descripción

El sistema de menús jerárquicos permite organizar los items de menú en una estructura de árbol con menús padres y submenús. Esto facilita la navegación cuando hay muchas opciones.

## Características

✅ **Menús Padres y Submenús**
- Los items pueden tener un menú padre
- Los items sin padre aparecen en el menú raíz
- Los menús padres se pueden expandir/contraer

✅ **Gestión Dinámica**
- Todo se configura en Django Admin
- No requiere cambios de código
- Los cambios se reflejan automáticamente

✅ **Control de Acceso**
- Cada item tiene sus propios roles permitidos
- Los submenús solo aparecen si el usuario tiene acceso
- Los menús padres solo se muestran si tienen al menos un submenu visible

✅ **Interfaz Amigable**
- Iconos Font Awesome para cada item
- Animación de chevron al expandir/contraer
- Estilos visuales diferenciados para submenús

## Estructura del Modelo

```python
class MenuItemRol(models.Model):
    # Campo principal
    url_name = CharField()              # Nombre de la URL en urls.py
    nombre_mostrado = CharField()       # Nombre que se muestra en el menú
    icono = CharField()                 # Clase Font Awesome (ej: fas fa-home)
    
    # Jerarquía
    menu_padre = ForeignKey('self')     # Referencia al menú padre (NULL = item raíz)
    
    # Control de acceso
    roles_permitidos = ManyToMany()     # Roles que pueden ver este item
    
    # Configuración
    orden = IntegerField()              # Orden de aparición
    activo = BooleanField()             # Si está activo o no
    es_submenu = BooleanField()         # Indica si es un submenu (legacy)
```

## Cómo Usar

### 1. Crear un Menú Padre

En Django Admin → Inventario → Menu Item Rol:

1. Click en "Agregar Menu Item Rol"
2. Llenar los campos:
   - **Menú Item**: `administracion` (único, sin espacios)
   - **Nombre Mostrado**: `Administración`
   - **URL Name**: `administracion`
   - **Icono**: `fas fa-cog`
   - **Menú Padre**: Dejar vacío (es un menú raíz)
   - **Orden**: 10
   - **Activo**: ✓
3. Click en "Guardar"

### 2. Crear un Submenú

1. Click en "Agregar Menu Item Rol"
2. Llenar los campos:
   - **Menú Item**: `lista_usuarios`
   - **Nombre Mostrado**: `Usuarios`
   - **URL Name**: `lista_usuarios`
   - **Icono**: `fas fa-users`
   - **Menú Padre**: Seleccionar "Administración"
   - **Orden**: 1
   - **Activo**: ✓
3. Asignar roles permitidos
4. Click en "Guardar"

### 3. Organizar Menús Automáticamente

Ejecutar el comando para agrupar items relacionados:

```bash
python manage.py organizar_menus_jerarquicos --dry-run
python manage.py organizar_menus_jerarquicos
```

Este comando:
- Crea menús padres automáticamente
- Asigna items a sus menús padres
- Agrupa por categorías lógicas

## Template Tags Disponibles

### `obtener_items_menu_principales`

Obtiene solo los items raíz (sin padre):

```django
{% load menu_tags %}
{% obtener_items_menu_principales user as menu_items %}
{% for item in menu_items %}
    {{ item.nombre_mostrado }}
{% endfor %}
```

### `obtener_submenus`

Obtiene los submenús de un menú padre:

```django
{% obtener_submenus menu_padre user as submenus %}
{% for submenu in submenus %}
    {{ submenu.nombre_mostrado }}
{% endfor %}
```

### `tiene_submenus` (filtro)

Verifica si un menú tiene submenús:

```django
{% if item|tiene_submenus:user %}
    <!-- Mostrar botón expandible -->
{% endif %}
```

### `contar_submenus` (filtro)

Cuenta cuántos submenús tiene un menú:

```django
{{ item|contar_submenus:user }}
```

## Template Incluido

El template `menu/menu_jerarquico.html` renderiza automáticamente:

- ✅ Menús padres con botón expandible
- ✅ Submenús anidados
- ✅ Animación de chevron
- ✅ Validación de acceso por rol
- ✅ Manejo de URLs inválidas

Se incluye en `base.html`:

```django
{% include "menu/menu_jerarquico.html" %}
```

## Estructura de Ejemplo

```
Dashboard (raíz)
├── Instituciones (raíz)
├── Productos (raíz)
├── Administración (padre)
│   ├── Usuarios (submenu)
│   ├── Roles (submenu)
│   ├── Opciones de Menú (submenu)
│   └── Reportes de Acceso (submenu)
├── Gestión de Inventario (padre)
│   ├── Lotes (submenu)
│   ├── Movimientos (submenu)
│   └── Alertas (submenu)
├── Entrada y Salida (padre)
│   ├── Entrada al Almacén (submenu)
│   └── Salidas (submenu)
├── Conteo Físico (padre)
│   ├── Buscar Lote (submenu)
│   └── Historial (submenu)
└── Reportes (padre)
    ├── Reporte General (submenu)
    ├── Análisis (submenu)
    └── Estadísticas (submenu)
```

## Estilos CSS

Los submenús tienen estilos especiales:

```css
.nav-link-submenu {
    padding-left: 2rem;      /* Indentación */
    font-size: 0.95rem;      /* Más pequeño */
}

.nav-link[data-bs-toggle="collapse"] {
    cursor: pointer;
}

.nav-link[data-bs-toggle="collapse"][aria-expanded="true"] i.fa-chevron-down {
    transform: rotate(180deg);  /* Chevron rotado */
}
```

## Comportamiento

### Cuando se Expande un Menú

1. El chevron rota 180°
2. Los submenús aparecen con animación
3. El estado se mantiene en la sesión

### Cuando se Oculta un Menú

1. El chevron vuelve a su posición original
2. Los submenús desaparecen
3. El estado se mantiene en la sesión

### Control de Acceso

- Si el usuario NO tiene acceso a ningún submenu, el menú padre NO se muestra
- Si el usuario tiene acceso a al menos un submenu, el menú padre se muestra
- Los submenús sin acceso se ocultan automáticamente

## Comandos Disponibles

### `organizar_menus_jerarquicos`

Organiza automáticamente los menús en una estructura jerárquica:

```bash
# Ver cambios sin aplicarlos
python manage.py organizar_menus_jerarquicos --dry-run

# Aplicar cambios
python manage.py organizar_menus_jerarquicos
```

### `validar_control_acceso`

Valida que todos los decoradores coincidan con MenuItemRol:

```bash
python manage.py validar_control_acceso --verbose
```

## Troubleshooting

### El menú padre no aparece

**Causa**: El usuario no tiene acceso a ningún submenu

**Solución**: 
1. Ir a Django Admin → Menu Item Rol
2. Editar el menú padre
3. Asignar roles permitidos a los submenús

### Los submenús no se expanden

**Causa**: Bootstrap no está cargado correctamente

**Solución**:
1. Verificar que Bootstrap 5 está en `base.html`
2. Verificar que JavaScript de Bootstrap está cargado
3. Revisar la consola del navegador para errores

### Un item no aparece en el menú

**Causa**: El usuario no tiene el rol asignado

**Solución**:
1. Ir a Django Admin → Usuarios
2. Editar el usuario
3. Asignar los grupos (roles) necesarios

## Mejores Prácticas

✅ **DO's**
- Usar nombres descriptivos para los menús padres
- Agrupar items relacionados bajo el mismo padre
- Usar iconos consistentes
- Mantener el orden lógico

❌ **DON'Ts**
- No crear más de 3 niveles de profundidad
- No mezclar categorías diferentes
- No usar nombres muy largos
- No cambiar URLs sin actualizar MenuItemRol

## Próximos Pasos

1. Ejecutar `organizar_menus_jerarquicos` para crear la estructura
2. Personalizar iconos en Django Admin
3. Ajustar el orden de los items
4. Probar con diferentes roles
5. Ajustar estilos CSS si es necesario
