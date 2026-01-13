# 📋 Reporte de Ubicaciones Vacías - Instrucciones de Instalación

## 📝 Descripción

Este reporte muestra todas las ubicaciones en los almacenes que **NO tienen lotes asignados**, permitiendo que el equipo de logística revise físicamente si están realmente vacías.

**Características:**
- ✅ Filtro por almacén
- ✅ Filtro por institución
- ✅ Filtro por código de ubicación
- ✅ Filtro por estado
- ✅ Exportación a Excel
- ✅ Exportación a PDF
- ✅ Paginación de resultados

---

## 🔧 Instalación

### Paso 1: Copiar Archivos

Copia los siguientes archivos a tu proyecto:

```bash
# Vista
cp inventario/views_reporte_ubicaciones_vacias.py /ruta/tu/proyecto/inventario/

# Template
cp inventario/templates/inventario/reporte_ubicaciones_vacias.html /ruta/tu/proyecto/inventario/templates/inventario/

# URLs
cp inventario/urls_reporte_ubicaciones_vacias.py /ruta/tu/proyecto/inventario/
```

### Paso 2: Agregar URLs

Abre `inventario/urls.py` (o el archivo principal de URLs) y agrega:

```python
# Al inicio del archivo, en los imports:
from .views_reporte_ubicaciones_vacias import (
    reporte_ubicaciones_vacias,
    exportar_ubicaciones_vacias_excel,
    exportar_ubicaciones_vacias_pdf,
)

# En la lista de urlpatterns:
urlpatterns = [
    # ... otras URLs ...
    
    # Reporte de Ubicaciones Vacías
    path('reportes/ubicaciones-vacias/', reporte_ubicaciones_vacias, name='reporte_ubicaciones_vacias'),
    path('reportes/ubicaciones-vacias/exportar-excel/', exportar_ubicaciones_vacias_excel, name='exportar_ubicaciones_vacias_excel'),
    path('reportes/ubicaciones-vacias/exportar-pdf/', exportar_ubicaciones_vacias_pdf, name='exportar_ubicaciones_vacias_pdf'),
]
```

### Paso 3: Verificar Dependencias

El reporte usa las siguientes librerías (que ya deberían estar instaladas):

```bash
# Si no están instaladas:
pip install openpyxl reportlab
```

### Paso 4: Agregar al Menú (Opcional)

Si tienes un menú de reportes, agrega un enlace:

```html
<a href="{% url 'reporte_ubicaciones_vacias' %}" class="dropdown-item">
    <i class="fas fa-warehouse"></i> Ubicaciones Vacías
</a>
```

---

## 🚀 Uso

### Acceder al Reporte

```
http://localhost:8000/reportes/ubicaciones-vacias/
```

### Filtros Disponibles

| Filtro | Descripción |
|--------|-------------|
| **Código de Ubicación** | Busca por código exacto o parcial |
| **Almacén** | Filtra por almacén específico |
| **Institución** | Filtra por institución |
| **Estado** | Disponible, Ocupada, Bloqueada, Cuarentena, Caducados, Devoluciones |

### Descargar Reportes

- **Excel**: Botón "Descargar Excel" (formato .xlsx)
- **PDF**: Botón "Descargar PDF" (formato .pdf)

---

## 📊 Información Mostrada

El reporte muestra las siguientes columnas:

| Columna | Descripción |
|---------|-------------|
| **ID** | Identificador único de la ubicación |
| **Código** | Código de la ubicación |
| **Descripción** | Descripción de la ubicación |
| **Nivel** | Nivel del rack (si aplica) |
| **Pasillo** | Número de pasillo |
| **Rack** | Número de rack |
| **Sección** | Sección dentro del almacén |
| **Almacén** | Nombre del almacén |
| **Institución** | Institución a la que pertenece |
| **Estado** | Estado actual de la ubicación |
| **Activo** | Si la ubicación está activa |

---

## 🔍 Consulta SQL Equivalente

Si deseas verificar los datos directamente en la BD:

```sql
SELECT 
    u.id,
    u.codigo,
    u.descripcion,
    u.nivel,
    u.pasillo,
    u.rack,
    u.seccion,
    a.nombre as almacen,
    i.denominacion as institucion,
    u.estado,
    u.activo
FROM inventario_ubicacionalmacen u
LEFT JOIN inventario_almacen a ON u.almacen_id = a.id
LEFT JOIN inventario_institucion i ON a.institucion_id = i.id
LEFT JOIN inventario_loteubicacion lu ON u.id = lu.ubicacion_id
WHERE lu.id IS NULL
ORDER BY u.codigo;
```

---

## 🛠️ Troubleshooting

### Error: "No module named 'reportlab'"

```bash
pip install reportlab
```

### Error: "No module named 'openpyxl'"

```bash
pip install openpyxl
```

### Error: "Template not found"

Asegúrate de que el archivo `reporte_ubicaciones_vacias.html` está en:
```
inventario/templates/inventario/reporte_ubicaciones_vacias.html
```

### Error: "Reverse for 'reporte_ubicaciones_vacias' not found"

Verifica que las URLs están correctamente agregadas en `urls.py`.

---

## 📈 Casos de Uso

1. **Auditoría de Almacén**: Verificar qué ubicaciones están realmente vacías
2. **Limpieza de Datos**: Identificar ubicaciones sin uso
3. **Planificación**: Saber dónde hay espacio disponible
4. **Reporte Gerencial**: Generar reportes para presentaciones

---

## 🔐 Permisos

El reporte requiere:
- ✅ Estar autenticado (`@login_required`)
- ✅ Acceso a modelos: `UbicacionAlmacen`, `LoteUbicacion`, `Almacen`, `Institucion`

---

## 📞 Soporte

Si tienes problemas:

1. Verifica que todos los archivos están en el lugar correcto
2. Revisa los logs de Django: `python manage.py runserver`
3. Asegúrate de que las dependencias están instaladas
4. Verifica que las URLs están correctamente configuradas

---

**Versión**: 1.0  
**Fecha**: 2026-01-12  
**Autor**: Sistema de Inventario Hospitalario
