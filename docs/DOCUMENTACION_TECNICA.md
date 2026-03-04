# Documentación Técnica – Sistema de Inventario Hospitalario

Documento técnico para entrega al área de sistemas: arquitectura, stack, despliegue, base de datos, configuración y seguridad.

---

## Tabla de contenidos

1. [Resumen ejecutivo](#1-resumen-ejecutivo)
2. [Arquitectura y stack tecnológico](#2-arquitectura-y-stack-tecnológico)
3. [Estructura del proyecto](#3-estructura-del-proyecto)
4. [Requisitos del sistema](#4-requisitos-del-sistema)
5. [Configuración y variables de entorno](#5-configuración-y-variables-de-entorno)
6. [Base de datos](#6-base-de-datos)
7. [Despliegue](#7-despliegue)
8. [Seguridad](#8-seguridad)
9. [Módulos principales y URLs](#9-módulos-principales-y-urls)
10. [Comandos de gestión](#10-comandos-de-gestión)
11. [Monitoreo y salud](#11-monitoreo-y-salud)
12. [Mantenimiento y respaldos](#12-mantenimiento-y-respaldos)
13. [Referencias y documentación de usuario](#13-referencias-y-documentación-de-usuario)

---

## 1. Resumen ejecutivo

| Aspecto | Descripción |
|--------|-------------|
| **Aplicación** | Sistema web de inventario hospitalario para gestión de productos, lotes, movimientos, pedidos, propuestas de suministro, picking, citas de proveedores, traslados, conteo físico y reportes. |
| **Framework** | Django 4.2 (Python 3.11). |
| **Base de datos** | PostgreSQL. |
| **Servidor de aplicación** | Gunicorn (producción); `runserver` (desarrollo). |
| **Contenedorización** | Docker (imagen Python 3.11 slim, arquitectura linux/amd64). |
| **Proxy / SSL** | Compatible con Nginx (reverse proxy, X-Forwarded-*). |

---

## 2. Arquitectura y stack tecnológico

### 2.1 Stack

| Componente | Tecnología |
|------------|------------|
| **Backend** | Django 4.2.16 |
| **Lenguaje** | Python 3.11 |
| **Base de datos** | PostgreSQL (psycopg2-binary 2.9.10) |
| **Configuración** | python-decouple, variables de entorno (os.getenv para BD) |
| **Formularios / UI** | Crispy Forms + Bootstrap 5 |
| **Exportación** | openpyxl (Excel), xhtml2pdf / WeasyPrint / ReportLab (PDF) |
| **Datos** | pandas (cargas masivas) |
| **Servidor WSGI** | Gunicorn 21.2.0 |
| **Imágenes** | Pillow |
| **APIs auxiliares** | Django REST Framework (uso puntual) |
| **Selectores avanzados** | django-select2 (opcional, puede estar comentado en INSTALLED_APPS) |

### 2.2 Diagrama de capas (conceptual)

```
[Cliente navegador]
        |
[Nginx / Reverse proxy]  ← SSL, static/media opcionales
        |
[Gunicorn / Django]      ← inventario_hospitalario.wsgi
        |
[PostgreSQL]             ← Base de datos principal
```

### 2.3 Aplicación Django

- **Proyecto**: `inventario_hospitalario` (settings, urls, wsgi).
- **App principal**: `inventario` (modelos, vistas, lógica de negocio, reportes, pedidos, logística, picking, etc.).
- **Usuario personalizado**: `inventario.User` (extends AbstractUser; campos adicionales: `clue`, `almacen`).

---

## 3. Estructura del proyecto

```
inventario_hospitalario/
├── inventario_hospitalario/     # Proyecto Django
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── context_processors.py
├── inventario/                  # App principal
│   ├── models.py                # Modelos base (User, Almacen, Producto, Lote, etc.)
│   ├── pedidos_models.py        # SolicitudPedido, PropuestaPedido, ItemPropuesta, LoteAsignado
│   ├── urls.py                  # URLs raíz de la app
│   ├── urls_fase2.py            # Logística: pedidos, propuestas, picking, citas, traslados, conteo
│   ├── pedidos_urls.py          # Rutas alternativas de pedidos (lista, crear, validar, reportes)
│   ├── pedidos_views.py         # Vistas de pedidos y propuestas
│   ├── propuesta_generator.py   # Generación automática de propuestas
│   ├── propuesta_utils.py       # Reservas, liberación, validación de disponibilidad
│   ├── fase5_utils.py           # Movimientos de inventario al surtir
│   ├── picking_views.py         # Picking por propuesta
│   ├── middleware.py            # Control de acceso por roles, logging, health check
│   ├── context_processors.py   # Permisos/contexto para templates
│   ├── management/commands/    # Comandos manage.py (cargar datos, roles, etc.)
│   ├── migrations/
│   └── templatetags/
├── templates/                   # Plantillas globales (base, login, registration)
├── static/                      # CSS, JS, imágenes (se recolectan en staticfiles)
├── media/                       # Archivos subidos por usuarios (desarrollo)
├── docs/                        # Documentación (manuales, técnico)
├── requirements.txt
├── manage.py
├── Dockerfile
├── docker-compose.yml
├── entrypoint.sh
├── .env.development / .env.production  # No versionar con datos sensibles
└── README.md
```

---

## 4. Requisitos del sistema

- **Python**: 3.11 (recomendado; la imagen Docker usa 3.11-slim).
- **PostgreSQL**: 12 o superior (recomendado).
- **Memoria**: Mínimo 1 GB RAM para el contenedor; 2 GB recomendado en producción.
- **Disco**: Espacio suficiente para `staticfiles`, `media`, logs y base de datos.
- **Dependencias del sistema (WeasyPrint/PDF)**: En la imagen Docker se instalan `libcairo2-dev`, `libpango`, etc.; en instalación manual pueden requerirse paquetes equivalentes según el SO.

---

## 5. Configuración y variables de entorno

La aplicación usa **python-decouple** (`config()`) y **os.getenv** para la base de datos. En producción no deben usarse valores por defecto sensibles; toda la configuración crítica debe venir de variables de entorno.

### 5.1 Variables utilizadas en `settings.py`

| Variable | Uso | Ejemplo / Notas |
|----------|-----|------------------|
| `SECRET_KEY` | Firma de sesiones y CSRF | Cadena larga y aleatoria; obligatoria en producción. |
| `DEBUG` | Modo depuración | `False` en producción. |
| `ALLOWED_HOSTS` | Hosts permitidos | Lista separada por comas (ej. `dominio.com,www.dominio.com`). |
| `CSRF_TRUSTED_ORIGINS` | Orígenes para CSRF (HTTPS) | Ej. `https://inventarios.ejemplo.com`. |
| `POSTGRES_DB` | Nombre de la base de datos | Ej. `inventario_bd`. |
| `POSTGRES_USER` | Usuario PostgreSQL | Ej. `postgres`. |
| `POSTGRES_PASSWORD` | Contraseña PostgreSQL | **No dejar por defecto en producción.** |
| `POSTGRES_HOST` | Host del servidor PostgreSQL | IP o hostname. |
| `POSTGRES_PORT` | Puerto PostgreSQL | Ej. `5432` o `5433`. |
| `USE_HTTPS` | Redirección HTTPS en producción | `True` si el proxy termina SSL. |
| `PORT` | Puerto expuesto (docker-compose) | Ej. `8700` para mapear al 8000 interno. |

### 5.2 Archivo `.env` de ejemplo (sin valores reales)

```env
DEBUG=False
SECRET_KEY=generar_clave_larga_aleatoria_aqui
ALLOWED_HOSTS=localhost,127.0.0.1,tu-dominio.com
CSRF_TRUSTED_ORIGINS=https://tu-dominio.com,http://localhost:8700

POSTGRES_DB=inventario_bd
POSTGRES_USER=postgres
POSTGRES_PASSWORD=XXXXXXXX
POSTGRES_HOST=ip_o_host_postgres
POSTGRES_PORT=5432

PORT=8700
USE_HTTPS=True
```

**Importante**: El archivo `.env` no debe versionarse con contraseñas ni claves reales. Usar `.env.example` como plantilla y documentar en este documento.

---

## 6. Base de datos

### 6.1 Motor y conexión

- **Engine**: `django.db.backends.postgresql`.
- **Conexión**: Definida en `settings.DATABASES['default']` usando las variables `POSTGRES_*`.

### 6.2 Modelos principales (resumen)

Los modelos están en `inventario.models` y `inventario.pedidos_models`:

- **User** (custom): usuario del sistema (clue, almacen).
- **Institucion, Almacen, UbicacionAlmacen**: instituciones y almacenes.
- **Producto, CategoriaProducto**: catálogo de productos (clave CNIS, etc.).
- **Lote, LoteUbicacion**: lotes y cantidades por ubicación; reservas.
- **MovimientoInventario**: movimientos de entrada/salida.
- **SolicitudPedido, ItemSolicitud**: pedidos (solicitudes) e ítems.
- **PropuestaPedido, ItemPropuesta, LoteAsignado**: propuestas de suministro y asignación a lotes/ubicaciones.
- **CitaProveedor, OrdenTraslado, ConteoFisico, DevolucionProveedor**, etc.: lógica de logística, citas, traslados, conteo y devoluciones.

### 6.3 Migraciones

- Las migraciones están en `inventario/migrations/`.
- **Aplicar**: `python manage.py migrate` (en el contenedor o entorno virtual).
- El `entrypoint.sh` del contenedor ejecuta `migrate --noinput` al arrancar.
- **Crear nuevas**: `python manage.py makemigrations inventario`.

### 6.4 Respaldo y restauración

- **Respaldo**: usar herramientas estándar de PostgreSQL (`pg_dump`) sobre la base configurada en `POSTGRES_*`.
- **Restauración**: según procedimiento del área de sistemas (crear BD, restaurar dump, verificar que el usuario de la app tenga permisos). El README del proyecto menciona sustituir tablas por un respaldo enviado por separado; debe documentarse el procedimiento exacto (ej. restaurar antes de la primera puesta en marcha).

---

## 7. Despliegue

### 7.1 Despliegue con Docker (recomendado)

1. **Requisitos**: Docker y Docker Compose instalados.
2. **Clonar el repositorio** y crear el archivo `.env` en la raíz con las variables necesarias (ver sección 5).
3. **Construir e iniciar**:
   ```bash
   docker-compose up -d --build
   ```
4. El servicio `web` expone el puerto definido en `PORT` (por defecto 8700) mapeado al 8000 interno.
5. La base de datos PostgreSQL **no** está definida en el `docker-compose.yml` mostrado; debe estar disponible en `POSTGRES_HOST` (servidor externo o otro contenedor/servicio).

### 7.2 Contenedor (Dockerfile)

- **Imagen base**: `python:3.11-slim`, plataforma `linux/amd64`.
- **Dependencias del sistema**: compilación y bibliotecas para PostgreSQL, Cairo, Pango (WeasyPrint/PDF).
- **Entrada**: `entrypoint.sh`:
  - Espera inicial (ej. 5 s) para que la BD esté disponible.
  - Ejecuta `migrate --noinput`.
  - Ejecuta `collectstatic --noinput --clear`.
  - Si `DEBUG` es False: inicia **Gunicorn** (bind 0.0.0.0:8000, 5 workers, timeout 120).
  - Si `DEBUG` es True: inicia **runserver** 0.0.0.0:8000.

### 7.3 Despliegue sin Docker (manual)

1. Python 3.11, entorno virtual, `pip install -r requirements.txt`.
2. Configurar variables de entorno (o archivo `.env` leído por python-decouple).
3. Crear y configurar la base PostgreSQL; ejecutar `migrate`.
4. Ejecutar `collectstatic` y servir `staticfiles` y `media` con el servidor web (Nginx/Apache).
5. En producción: usar Gunicorn (o similar) detrás del proxy; no usar `runserver`.

### 7.4 Proxy inverso (Nginx)

- La aplicación confía en los headers `X-Forwarded-Proto`, `X-Forwarded-Host`, `X-Forwarded-Port` (`USE_X_FORWARDED_* = True`).
- `SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')` para que Django considere la petición como HTTPS cuando el proxy termina SSL.
- En producción, configurar Nginx para:
  - Proxy pass al puerto de Gunicorn (ej. 8000).
  - Opcionalmente servir `/static/` y `/media/` desde disco.
  - Incluir los headers `X-Forwarded-*` adecuados.

---

## 8. Seguridad

### 8.1 Configuración en producción (cuando `DEBUG=False`)

- **SESSION_COOKIE_SECURE** y **CSRF_COOKIE_SECURE**: True.
- **SECURE_SSL_REDIRECT**: según `USE_HTTPS`.
- **SECURE_BROWSER_XSS_FILTER**: True.
- **SECURE_CONTENT_SECURITY_POLICY**: definida (scripts, estilos, fuentes, imágenes).
- **X_FRAME_OPTIONS**: SAMEORIGIN.
- **HSTS**: habilitado (SECURE_HSTS_*).

### 8.2 Autenticación y autorización

- **Login/Logout**: rutas estándar Django (`/login/`, `/logout/`).
- **Cambio de contraseña**: `/password_change/`, `/password_change/done/` (requieren autenticación).
- **Control de acceso**: middleware `ControlAccesoRolesMiddleware` que consulta `MenuItemRol` y restringe vistas según grupos/permisos; superusuario y ciertas URLs (login, logout, dashboard) están excluidas.
- **Contexto de roles**: `AgregarContextoAccesoMiddleware` agrega `request.roles_usuario` y `request.es_admin`.

### 8.3 Recomendaciones para el área de sistemas

- Mantener `SECRET_KEY` y `POSTGRES_PASSWORD` solo en entorno (o gestor de secretos); no en código ni en `.env` versionado.
- En producción: `DEBUG=False`, `ALLOWED_HOSTS` y `CSRF_TRUSTED_ORIGINS` ajustados al dominio real.
- Servir la aplicación solo por HTTPS en producción; configurar correctamente el proxy.
- Revisar permisos de la base de datos (usuario con mínimos privilegios necesarios).
- Evaluar políticas de respaldo, retención de logs y auditoría de accesos.

---

## 9. Módulos principales y URLs

| Módulo | Prefijo / Inclusión | Descripción |
|--------|----------------------|-------------|
| **Dashboard** | `/` | Página principal (requiere login). |
| **Health / Diagnóstico** | `/health/`, `/diagnostico/` | Comprobación de estado y diagnóstico del sistema. |
| **Instituciones** | `/instituciones/` | CRUD instituciones (CLUE). |
| **Productos** | `/productos/` | CRUD catálogo de productos. |
| **Lotes** | `/lotes/` | CRUD lotes y ubicaciones. |
| **Movimientos** | `/movimientos/` | Listado y detalle de movimientos de inventario. |
| **Carga masiva** | `/carga-masiva/`, `/carga-masiva/ubicaciones-almacen/`, etc. | Cargas masivas por Excel. |
| **Logística (Fase 2)** | `/logistica/` | Citas, traslados, conteo físico, **pedidos**, **propuestas**, picking, acuse. |
| **Pedidos (alternativo)** | `/pedidos/` | Lista, crear, validar, editar, cancelar; reportes de pedidos. |
| **Picking** | `/picking/` | Dashboard y redirección a picking por propuesta en logística. |
| **Devoluciones** | `/devoluciones/` | Devoluciones a proveedores. |
| **Reportes** | `/reportes/`, `/reportes/salidas/`, etc. | Reportes de existencias, movimientos, reservas, pedidos, etc. |
| **Sistema** | `/sistema/logs/` | Logs del sistema. |
| **Admin Django** | `/admin/` | Panel de administración. |
| **Admin roles** | `/admin-roles/` | Gestión de roles y menús. |
| **Autenticación** | `/login/`, `/logout/`, `/password_change/`, etc. | Login, logout, cambio de contraseña, reset. |

Las URLs de **pedidos y propuestas** (crear, validar, editar, detalle, cancelar, picking, surtir) están bajo `/logistica/` (urls_fase2) y opcionalmente bajo `/pedidos/` (pedidos_urls). Ver `docs/MANUAL_PEDIDOS.md` para flujos de usuario.

---

## 10. Comandos de gestión

Ejecutar con `python manage.py <comando>` (o dentro del contenedor: `docker-compose exec web python manage.py <comando>`).

| Comando | Descripción |
|---------|-------------|
| `migrate` | Aplicar migraciones. |
| `makemigrations inventario` | Generar migraciones tras cambios en modelos. |
| `collectstatic --noinput` | Recolectar estáticos en `staticfiles`. |
| `createsuperuser` | Crear superusuario. |
| `cargar_menu_roles` | Sincronizar menús y roles. |
| `sincronizar_menuitemrol` | Sincronizar ítems de menú con roles. |
| `cargar_ubicaciones` | Cargar ubicaciones de almacén. |
| `cargar_clues` | Cargar instituciones (CLUE). |
| `cargar_inventario` | Carga de inventario. |
| `cargar_lotes_masivo` | Carga masiva de lotes. |
| `cargar_ordenes_suministro` | Cargar órdenes de suministro. |
| `crear_grupos_permisos` / `crear_roles` | Crear grupos y permisos. |
| `sincronizar_cantidades` | Sincronizar cantidades (lotes/ubicaciones). |
| `validar_control_acceso` | Validar configuración de control de acceso. |
| `limpiar_lotes_asignados_duplicados` | Limpieza de duplicados en asignaciones. |

Otros comandos en `inventario/management/commands/` pueden documentarse internamente según necesidad.

---

## 11. Monitoreo y salud

- **Health check**: `GET /health/` — responde si la aplicación está viva (el middleware `HealthCheckMiddleware` puede excluir esta ruta de lógica pesada).
- **Diagnóstico**: `GET /diagnostico/` — página de diagnóstico del sistema (conexión BD, etc.); restringir en producción solo a personal autorizado.
- **Logs**: salida estándar (console); en Docker los logs se capturan con `docker-compose logs`. La configuración de `LOGGING` en `settings.py` define formateo y loggers para `django` e `inventario`.
- **Request logging**: `RequestLoggingMiddleware` y `LoggingMiddleware` registran peticiones y errores (consultar implementación en `inventario/middleware.py`).

---

## 12. Mantenimiento y respaldos

- **Base de datos**: respaldos periódicos de PostgreSQL (pg_dump); definir política con el área de sistemas.
- **Archivos subidos**: el directorio `media/` debe incluirse en respaldos si se almacenan documentos o imágenes importantes.
- **Estáticos**: `staticfiles/` se regenera con `collectstatic`; no es crítico respaldarlo si el código fuente está versionado.
- **Logs**: definir retención y almacenamiento de logs (contenedor, servidor, agregador) según políticas de la organización.
- **Actualizaciones**: probar en entorno de staging; aplicar migraciones en ventana de mantenimiento si es necesario; revisar `requirements.txt` y dependencias con CVE conocidos.

---

## 13. Referencias y documentación de usuario

| Documento | Ubicación | Contenido |
|-----------|-----------|-----------|
| **Manual de pedidos** | `docs/MANUAL_PEDIDOS.md` | Flujo de pedidos, carga CSV, validación, propuestas, edición, aprobación, picking, surtimiento, cancelaciones. |
| **Manual gestión de pedidos (Fase 2.2.1)** | `docs/MANUAL_USUARIO_GESTION_PEDIDOS.md` | Roles, flujo general, crear/validar solicitudes, gestionar propuestas. |
| **Manual de pedidos (resumido)** | `docs/MANUAL_USUARIO_PEDIDOS.md` | Vista rápida de funcionalidades de pedidos. |
| **Fase 5 movimientos** | `docs/FASE5_MOVIMIENTOS_SUMINISTRO.md` | Detalle de movimientos al surtir. |
| **Otros manuales** | `docs/` | Citologicos, devoluciones, llegadas, reportes, etc. |

---

## Control de versiones del documento

| Fecha | Versión | Descripción |
|-------|---------|-------------|
| (Actual) | 1.0 | Documentación técnica inicial para entrega al área de sistemas. |

Para dudas sobre la aplicación o este documento, contactar al equipo de desarrollo o al responsable del proyecto.
