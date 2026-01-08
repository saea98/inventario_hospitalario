# Dashboard de Reportes de Conteos Físicos

## Descripción

Se ha creado un dashboard completo para visualizar y reportar los conteos físicos realizados. El dashboard incluye:

✅ **Gráficos de Resumen**
- Pie chart: Distribución por progreso (1/3, 2/3, 3/3)
- Donut chart: Estado de conteos (Completados vs En Progreso)
- Bar charts: Conteos por almacén y usuario

✅ **Tarjetas de Estadísticas**
- Total de conteos
- Conteos completados (3/3)
- Conteos en progreso (1/3 o 2/3)
- Porcentaje completado

✅ **Filtros Avanzados**
- Por fecha (desde/hasta)
- Por almacén
- Por estado (completado, en progreso, todos)
- Por usuario

✅ **Tabla Detallada**
- CLAVE (CNIS)
- PRODUCTO
- LOTE
- UBICACIÓN
- PROGRESO (1/3, 2/3, 3/3)
- COMPLETADO (Sí/No)
- USUARIO
- FECHA
- VALORES DE CONTEOS (1er, 2do, 3er)

✅ **Exportación**
- A Excel (.xlsx)
- A PDF

---

## Instalación y Configuración

### 1. Hacer Pull del Código

```bash
cd ~/inventario/inventario_hospitalario
git pull origin main
```

### 2. Reiniciar el Contenedor

```bash
docker-compose restart inventario_dev_2
```

### 3. Acceder al Dashboard

**URL**: `http://localhost:8700/logistica/conteos/dashboard/`

O desde el menú: **Logística → Conteo Físico → Dashboard de Conteos**

---

## Agregar al Menú (Opción 1: Automático)

Si quieres que aparezca en el menú automáticamente, ejecuta este comando:

```bash
docker exec inventario_dev_2 python manage.py shell
```

Luego en el shell de Django:

```python
from django.contrib.auth.models import Group
from inventario.models import MenuItemRol

# Obtener los roles que pueden acceder
almacenero = Group.objects.get(name='Almacenero')
admin = Group.objects.get(name='Administrador')
gestor = Group.objects.get(name='Gestor de Inventario')
supervision = Group.objects.get(name='Supervisión')

# Crear el menú
menu_dashboard = MenuItemRol.objects.create(
    menu_item='dashboard_conteos',
    nombre_mostrado='Dashboard de Conteos',
    icono='fas fa-chart-bar',
    url_name='conteo_fisico:dashboard',
    orden=10,
    activo=True,
    es_submenu=True
)

# Asignar roles
menu_dashboard.roles_permitidos.add(almacenero, admin, gestor, supervision)
menu_dashboard.save()

print("✅ Dashboard agregado al menú correctamente")
exit()
```

---

## Agregar al Menú (Opción 2: Admin)

1. Accede a `http://localhost:8700/admin/`
2. Ve a **Inventario → Menu Item Roles**
3. Haz clic en **Agregar Menu Item Rol**
4. Completa los campos:
   - **Opción de Menú**: `dashboard_conteos`
   - **Nombre Mostrado**: `Dashboard de Conteos`
   - **Icono Font Awesome**: `fas fa-chart-bar`
   - **Nombre de URL**: `conteo_fisico:dashboard`
   - **Roles Permitidos**: Selecciona Almacenero, Administrador, Gestor de Inventario, Supervisión
   - **Orden**: 10
   - **Activo**: ✓
   - **Es Submenú**: ✓
5. Haz clic en **Guardar**

---

## Uso del Dashboard

### Filtrar Conteos

1. Selecciona el rango de fechas (Desde/Hasta)
2. Selecciona el almacén (opcional)
3. Selecciona el estado (Todos, Completados, En Progreso)
4. Selecciona el usuario (opcional)
5. Haz clic en **Filtrar**

### Exportar Datos

**Excel**:
- Haz clic en el botón **Exportar Excel**
- Se descargará un archivo `.xlsx` con todos los conteos filtrados

**PDF**:
- Haz clic en el botón **Exportar PDF**
- Se descargará un archivo `.pdf` con los primeros 50 conteos filtrados

---

## Estructura de Archivos

```
inventario/
├── views_dashboard_conteos.py          # Vistas del dashboard
├── urls_conteo_fisico.py               # URLs actualizadas
└── migrations/
    └── 0042_add_registro_conteo_fisico.py

templates/
└── inventario/
    └── dashboard_conteos.html          # Template del dashboard
```

---

## Funciones Principales

### `dashboard_conteos(request)`
- Renderiza el dashboard con gráficos y tabla
- Aplica filtros según parámetros GET
- Calcula estadísticas

### `exportar_conteos_excel(request)`
- Exporta conteos filtrados a Excel
- Incluye estilos y bordes
- Ajusta ancho de columnas automáticamente

### `exportar_conteos_pdf(request)`
- Exporta conteos filtrados a PDF
- Limita a 50 registros por PDF
- Incluye información del reporte

---

## Requisitos

✅ Django 4.2+
✅ openpyxl (para Excel)
✅ reportlab (para PDF)
✅ Chart.js (incluido en CDN)
✅ Bootstrap 5 (incluido en CDN)

---

## Notas Importantes

1. **Permisos**: Solo usuarios con roles específicos pueden acceder al dashboard
2. **Rendimiento**: Si hay muchos conteos, la tabla se limita a 100 registros
3. **Exportación PDF**: Se limita a 50 registros para evitar archivos muy grandes
4. **Gráficos**: Se actualizan automáticamente según los filtros aplicados

---

## Solución de Problemas

### Error: "No module named 'openpyxl'"
```bash
docker exec inventario_dev_2 pip install openpyxl
```

### Error: "No module named 'reportlab'"
```bash
docker exec inventario_dev_2 pip install reportlab
```

### El dashboard no aparece en el menú
- Verifica que hayas agregado el registro en `MenuItemRol`
- Verifica que tu usuario tenga uno de los roles permitidos
- Recarga la página (Ctrl+F5)

### Los gráficos no se muestran
- Verifica que tengas conexión a internet (Chart.js se carga desde CDN)
- Abre la consola del navegador (F12) y busca errores

---

## Próximas Mejoras (Opcional)

- [ ] Agregar filtro por rango de cantidad
- [ ] Agregar gráfico de tendencia temporal
- [ ] Agregar comparación de conteos (diferencias)
- [ ] Agregar notificaciones de conteos pendientes
- [ ] Agregar descarga de reportes programados

---

## Contacto y Soporte

Para reportar problemas o sugerencias, contacta al equipo de desarrollo.
