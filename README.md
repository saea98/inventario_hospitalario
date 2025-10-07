# Sistema de Inventario Hospitalario

Una aplicación web completa desarrollada en Django para la gestión de inventarios en instituciones de salud, con soporte para control de lotes, fechas de caducidad, trazabilidad y reportes.

## Características Principales

### 🏥 Gestión de Instituciones
- Catálogo completo de instituciones de salud (CLUES)
- Organización por alcaldías y tipos de institución
- Información de contacto y ubicación
- Estados activo/inactivo

### 💊 Catálogo de Productos
- Gestión de productos médicos e insumos
- Clasificación por categorías
- Códigos CNIS y descripciones detalladas
- Precios de referencia
- Marcado de insumos CPM

### 📦 Control de Inventario
- Gestión de lotes por institución
- Control de fechas de fabricación y caducidad
- Estados de lote (Disponible, Suspendido, Deteriorado, Caducado)
- Trazabilidad completa de movimientos
- Cálculo automático de valores

### ⚠️ Sistema de Alertas
- Alertas automáticas de productos próximos a caducar
- Notificaciones de productos caducados
- Alertas de bajo stock
- Dashboard de alertas por prioridad

### 📊 Reportes y Análisis
- Reportes de inventario en Excel
- Reportes de movimientos
- Reportes de caducidades
- Estadísticas del dashboard
- Filtros avanzados

### 📁 Carga de Archivos
- Importación de archivos Excel de CLUES
- Importación de inventarios desde Excel
- Procesamiento automático con validaciones
- Log de errores detallado

## Tecnologías Utilizadas

- **Backend**: Django 4.2.16
- **Base de Datos**: SQLite (desarrollo) / PostgreSQL (producción)
- **Frontend**: Bootstrap 5, HTML5, CSS3, JavaScript
- **Formularios**: Django Crispy Forms con Bootstrap 5
- **Procesamiento Excel**: pandas, openpyxl
- **Autenticación**: Sistema de usuarios de Django
- **Reportes**: Generación de Excel con pandas

## Instalación y Configuración

### Prerrequisitos
- Python 3.11+
- pip
- Entorno virtual (recomendado)

### Pasos de Instalación

1. **Clonar el repositorio**
```bash
git clone <url-del-repositorio>
cd inventario_hospitalario
```

2. **Crear y activar entorno virtual**
```bash
python3.11 -m venv venv
source venv/bin/activate  # En Linux/Mac
# o
venv\Scripts\activate  # En Windows
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

4. **Configurar variables de entorno**
```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

5. **Ejecutar migraciones**
```bash
python manage.py migrate
```

6. **Cargar datos de demostración**
```bash
python manage.py cargar_datos_demo
```

7. **Crear superusuario**
```bash
python manage.py createsuperuser
```

8. **Iniciar servidor de desarrollo**
```bash
python manage.py runserver
```

La aplicación estará disponible en `http://localhost:8000`

## Estructura del Proyecto

```
inventario_hospitalario/
├── inventario/                 # Aplicación principal
│   ├── models.py              # Modelos de datos
│   ├── views.py               # Vistas principales
│   ├── views_extras.py        # Vistas adicionales
│   ├── forms.py               # Formularios
│   ├── admin.py               # Configuración del admin
│   ├── utils.py               # Utilidades y procesadores
│   ├── reports.py             # Generadores de reportes
│   ├── urls.py                # Configuración de URLs
│   └── management/            # Comandos personalizados
├── templates/                 # Plantillas HTML
│   ├── base.html             # Plantilla base
│   ├── inventario/           # Plantillas de la app
│   └── registration/         # Plantillas de autenticación
├── static/                   # Archivos estáticos
├── media/                    # Archivos subidos
├── requirements.txt          # Dependencias
├── .env                      # Variables de entorno
└── manage.py                 # Script de gestión de Django
```

## Modelos de Datos

### Principales Entidades

- **Alcaldia**: Demarcaciones territoriales
- **TipoInstitucion**: Tipos de instituciones de salud
- **Institucion**: Instituciones de salud (CLUES)
- **CategoriaProducto**: Categorías de productos médicos
- **Producto**: Productos/medicamentos/insumos
- **Proveedor**: Proveedores de productos
- **FuenteFinanciamiento**: Fuentes de financiamiento
- **OrdenSuministro**: Órdenes de suministro
- **Lote**: Lotes de productos por institución
- **MovimientoInventario**: Movimientos de inventario
- **AlertaCaducidad**: Alertas de caducidad
- **CargaInventario**: Registro de cargas de archivos

## Funcionalidades Principales

### Dashboard
- Estadísticas generales del sistema
- Alertas de caducidad y bajo stock
- Últimos movimientos de inventario
- Top instituciones por valor de inventario
- Acciones rápidas

### Gestión de Instituciones
- Lista con filtros y búsqueda
- Creación y edición de instituciones
- Vista detallada con estadísticas
- Importación desde archivo CLUES

### Gestión de Productos
- Catálogo completo con filtros
- Creación y edición de productos
- Vista detallada con distribución por institución
- Categorización y precios de referencia

### Control de Inventario
- Lista de lotes con filtros avanzados
- Creación y edición de lotes
- Trazabilidad de movimientos
- Control de estados y fechas

### Sistema de Alertas
- Productos caducados
- Próximos a caducar (30, 60, 90 días)
- Bajo stock
- Priorización por criticidad

### Reportes
- Reporte general de inventario
- Reporte de movimientos
- Reporte de caducidades
- Exportación a Excel
- Filtros personalizables

## Usuarios y Permisos

### Tipos de Usuario
- **Superusuario**: Acceso completo al sistema
- **Usuario Estándar**: Acceso a funcionalidades principales
- **Usuario de Solo Lectura**: Solo consulta (futuro)

### Credenciales de Prueba
- **Usuario**: admin
- **Contraseña**: admin123

## Configuración de Producción

### Variables de Entorno
```env
DEBUG=False
SECRET_KEY=tu-clave-secreta-muy-segura
DATABASE_URL=postgresql://usuario:password@host:puerto/basedatos
ALLOWED_HOSTS=tu-dominio.com,www.tu-dominio.com
```

### Base de Datos PostgreSQL
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'inventario_hospitalario',
        'USER': 'tu_usuario',
        'PASSWORD': 'tu_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

## Formato de Archivos Excel

### Archivo CLUES.xlsx
Columnas requeridas:
- CLUE
- IB CLUE
- DENOMINACIÓN
- ALCALDÍA
- TIPO

### Archivo inventario_hospital.xlsx
Columnas requeridas:
- CLAVE/CNIS
- DESCRIPCIÓN
- LOTE
- CANTIDAD
- PRECIO UNITARIO
- FECHA DE CADUCIDAD
- FECHA DE FABRICACIÓN
- ESTADO

## API Endpoints

### Estadísticas
- `GET /api/estadisticas/` - Estadísticas del dashboard

### Reportes
- `GET /reportes/inventario/excel/` - Reporte de inventario
- `GET /reportes/movimientos/excel/` - Reporte de movimientos
- `GET /reportes/caducidades/excel/` - Reporte de caducidades

## Contribución

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## Soporte

Para soporte técnico o preguntas sobre el sistema:
- Crear un issue en el repositorio
- Contactar al equipo de desarrollo

## Roadmap

### Próximas Funcionalidades
- [ ] API REST completa
- [ ] Notificaciones por email
- [ ] Dashboard con gráficos interactivos
- [ ] Módulo de transferencias entre instituciones
- [ ] Integración con códigos de barras
- [ ] App móvil
- [ ] Reportes automáticos programados
- [ ] Integración con sistemas externos

## Changelog

### v1.0.0 (2025-01-03)
- Versión inicial del sistema
- Gestión completa de inventarios
- Sistema de alertas
- Reportes en Excel
- Carga de archivos
- Dashboard administrativo
# inventario_hospitalario
