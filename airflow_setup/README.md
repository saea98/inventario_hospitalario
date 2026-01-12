# 🚀 Airflow - Sistema de Actualización de Lotes Caducados

Sistema automatizado que revisa y actualiza lotes caducados en el inventario hospitalario usando Apache Airflow.

## 📋 Características

- ✅ Ejecución diaria automática (2:00 AM)
- ✅ Identificación de lotes caducados
- ✅ Marcado como no disponible
- ✅ Registro de cambios en auditoría
- ✅ Notificaciones por Telegram
- ✅ Interfaz web de monitoreo
- ✅ Monitor de tareas (Flower)

## 🏗️ Estructura del Proyecto

```
airflow_setup/
├── dags/
│   └── actualizar_lotes_caducados.py    # DAG principal
├── logs/                                 # Logs de ejecución
├── plugins/                              # Plugins personalizados
├── config/
│   └── airflow.cfg                       # Configuración de Airflow
├── docker-compose.yml                    # Orquestación de contenedores
├── Dockerfile                            # Imagen personalizada
├── requirements.txt                      # Dependencias Python
├── .env                                  # Variables de entorno
├── init_airflow.sh                       # Script de inicialización
├── configure_airflow.py                  # Configurador interactivo
└── README.md                             # Este archivo
```

## 🔧 Requisitos Previos

- Docker y Docker Compose instalados
- PostgreSQL con la BD del inventario corriendo
- Token de Bot de Telegram (opcional pero recomendado)
- Chat ID de Telegram (opcional pero recomendado)

## 📦 Instalación

### 1. Preparar el Entorno

```bash
cd ~/inventario_hospitalario/airflow_setup

# Crear directorios necesarios
mkdir -p dags logs plugins config

# Dar permisos
chmod +x init_airflow.sh configure_airflow.py
```

### 2. Configurar Variables de Entorno

Edita el archivo `.env` con tus valores:

```bash
nano .env
```

**Variables importantes:**

```env
# Base de datos del inventario
DB_HOST=host.docker.internal          # o la IP de tu servidor
DB_PORT=5432
DB_NAME=inventario_hospitalario
DB_USER=postgres
DB_PASSWORD=tu_contraseña

# Telegram (obtener en siguiente sección)
TELEGRAM_BOT_TOKEN=tu_token_aqui
TELEGRAM_CHAT_ID=tu_chat_id_aqui
```

### 3. Obtener Credenciales de Telegram (Opcional)

#### Crear Bot de Telegram:

1. Abre Telegram y busca **@BotFather**
2. Envía el comando `/start`
3. Envía `/newbot`
4. Sigue las instrucciones para crear tu bot
5. **Copia el token** que te proporciona (ej: `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`)

#### Obtener Chat ID:

1. Abre Telegram y busca **@userinfobot**
2. Envía `/start`
3. Te mostrará tu **User ID** (este es tu Chat ID)
4. O envía un mensaje a tu bot y accede a:
   ```
   https://api.telegram.org/bot<TOKEN>/getUpdates
   ```
   Busca `"chat":{"id":123456789}` (ese es tu Chat ID)

### 4. Iniciar Airflow

```bash
# Opción A: Inicialización automática
docker-compose up -d
sleep 30
bash init_airflow.sh

# Opción B: Configuración interactiva
docker-compose up -d
sleep 30
python3 configure_airflow.py
```

### 5. Verificar la Instalación

```bash
# Ver estado de los contenedores
docker-compose ps

# Ver logs
docker-compose logs -f airflow-webserver

# Verificar que el DAG está cargado
docker exec airflow_webserver airflow dags list
```

## 🌐 Acceso a Interfaces

| Servicio | URL | Usuario | Contraseña |
|----------|-----|---------|-----------|
| Airflow Web | http://localhost:8080 | admin | admin |
| Flower (Monitor) | http://localhost:5555 | - | - |
| PostgreSQL Airflow | localhost:5433 | airflow | airflow |

## 🎯 Uso del DAG

### Activar el DAG

1. Accede a http://localhost:8080
2. Busca el DAG **"actualizar_lotes_caducados"**
3. Haz clic en el toggle para activarlo
4. El DAG se ejecutará diariamente a las **2:00 AM**

### Ejecutar Manualmente

```bash
# Ejecutar el DAG ahora
docker exec airflow_webserver airflow dags test actualizar_lotes_caducados 2024-01-12

# O desde la interfaz web:
# 1. Abre el DAG
# 2. Haz clic en "Trigger DAG"
```

### Monitorear Ejecuciones

1. **Airflow Web**: http://localhost:8080
   - Ver estado de tareas
   - Revisar logs
   - Monitorear duración

2. **Flower**: http://localhost:5555
   - Monitorear workers
   - Ver tareas en cola
   - Estadísticas de ejecución

## 📊 Estructura del DAG

El DAG ejecuta las siguientes tareas en orden:

```
obtener_lotes_caducados
        ↓
actualizar_lotes_caducados
        ↓
    ┌───┴────┐
    ↓        ↓
enviar_notificacion_telegram  registrar_resumen
```

### Tareas Detalladas

#### 1. **obtener_lotes_caducados**
- Conecta a PostgreSQL
- Busca lotes con `fecha_caducidad < HOY`
- Filtra lotes que no estén ya marcados como caducados
- Retorna lista de lotes encontrados

#### 2. **actualizar_lotes_caducados**
- Marca lotes como `disponible = false`
- Cambia estado a `'caducado'`
- Registra en tabla de auditoría
- Retorna cantidad de actualizaciones

#### 3. **enviar_notificacion_telegram**
- Construye mensaje con resumen
- Envía por Telegram (máximo 10 lotes en el mensaje)
- No falla el DAG si hay error en Telegram

#### 4. **registrar_resumen**
- Registra timestamp de ejecución
- Cantidad de lotes procesados
- Estado final del DAG

## 🔍 Monitoreo y Logs

### Ver Logs de una Tarea

```bash
# Desde Docker
docker exec airflow_webserver airflow tasks logs \
    actualizar_lotes_caducados \
    obtener_lotes_caducados \
    2024-01-12

# O desde la interfaz web:
# 1. Abre el DAG
# 2. Haz clic en una tarea
# 3. Haz clic en "Log"
```

### Logs en el Sistema de Archivos

```bash
# Logs de Airflow
ls -la airflow_setup/logs/

# Logs específicos del DAG
ls -la airflow_setup/logs/actualizar_lotes_caducados/
```

## 🔐 Seguridad

### Cambiar Contraseña del Admin

```bash
docker exec airflow_webserver airflow users update \
    --username admin \
    --password nueva_contraseña
```

### Crear Usuario Adicional

```bash
docker exec airflow_webserver airflow users create \
    --username usuario \
    --firstname Nombre \
    --lastname Apellido \
    --role Viewer \
    --email usuario@example.com \
    --password contraseña
```

### Roles Disponibles

- **Admin**: Acceso total
- **User**: Puede ejecutar y monitorear DAGs
- **Viewer**: Solo lectura
- **Op**: Operaciones

## 🛠️ Troubleshooting

### Error: "No se puede conectar a la base de datos"

**Solución:**
```bash
# Verificar que PostgreSQL está corriendo
docker ps | grep postgres

# Verificar conectividad desde Airflow
docker exec airflow_webserver psql -h host.docker.internal -U postgres -d inventario_hospitalario -c "SELECT 1"

# Si usas Linux, reemplaza host.docker.internal con:
# - IP de la red Docker: docker inspect -f '{{range.NetworkSettings.Networks}}{{.Gateway}}{{end}}' nombre_contenedor
# - Nombre del contenedor: postgres_inventario
```

### Error: "Telegram token inválido"

**Solución:**
```bash
# Verificar token
docker exec airflow_webserver airflow variables get TELEGRAM_BOT_TOKEN

# Actualizar token
docker exec airflow_webserver airflow variables set TELEGRAM_BOT_TOKEN "nuevo_token"

# Probar conexión
curl -X GET "https://api.telegram.org/botTOKEN/getMe"
```

### El DAG no aparece en Airflow

**Solución:**
```bash
# Verificar que el archivo DAG está en la carpeta correcta
ls -la dags/

# Recargar DAGs
docker exec airflow_webserver airflow dags reserialize

# Reiniciar scheduler
docker-compose restart airflow-scheduler
```

### Las tareas no se ejecutan

**Solución:**
```bash
# Verificar que el scheduler está corriendo
docker-compose ps | grep scheduler

# Verificar que el worker está corriendo
docker-compose ps | grep worker

# Reiniciar servicios
docker-compose restart airflow-scheduler airflow-worker

# Ver estado de Redis
docker exec redis redis-cli ping
```

## 📝 Configuración Avanzada

### Cambiar Horario de Ejecución

Edita `dags/actualizar_lotes_caducados.py`:

```python
# Línea 35: Cambiar schedule_interval
schedule_interval='0 2 * * *',  # Actual: 2:00 AM diariamente

# Ejemplos:
# '0 0 * * *'      - Medianoche
# '0 */6 * * *'    - Cada 6 horas
# '0 0 * * 1'      - Lunes a medianoche
# '0 0 1 * *'      - Primer día del mes
```

### Agregar Más Notificaciones

Edita `dags/actualizar_lotes_caducados.py` y agrega una nueva tarea:

```python
def enviar_email(**context):
    """Envía email con el resumen"""
    # Tu código aquí
    pass

tarea_email = PythonOperator(
    task_id='enviar_email',
    python_callable=enviar_email,
    provide_context=True,
    dag=dag,
)

# Agregar a la cadena de ejecución
tarea_actualizar >> [tarea_notificar, tarea_email, tarea_resumen]
```

### Aumentar Reintentos

Edita `dags/actualizar_lotes_caducados.py`:

```python
default_args = {
    'retries': 5,  # Aumentar de 2 a 5
    'retry_delay': timedelta(minutes=10),  # Aumentar delay
}
```

## 🚀 Deployment en Producción

### Consideraciones

1. **Usar imagen personalizada**: Descomenta en `docker-compose.yml`
   ```yaml
   image: airflow:custom
   build: .
   ```

2. **Usar PostgreSQL externa**: Cambiar `postgres-airflow` por conexión remota

3. **Configurar backups**: Hacer backup de `postgres_airflow_data`

4. **Monitoreo**: Integrar con sistemas de monitoreo (Prometheus, etc.)

5. **SSL/TLS**: Configurar certificados para Airflow

### Script de Backup

```bash
#!/bin/bash
# backup_airflow.sh

BACKUP_DIR="/backups/airflow"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup de PostgreSQL
docker exec postgres_airflow pg_dump -U airflow airflow > \
    $BACKUP_DIR/airflow_db_$DATE.sql

# Backup de logs
tar -czf $BACKUP_DIR/airflow_logs_$DATE.tar.gz logs/

# Backup de DAGs
tar -czf $BACKUP_DIR/airflow_dags_$DATE.tar.gz dags/

echo "Backup completado: $DATE"
```

## 📞 Soporte

Para problemas o preguntas:

1. Revisar logs: `docker-compose logs -f`
2. Verificar conectividad: `docker exec airflow_webserver ping host.docker.internal`
3. Probar DAG manualmente: `docker exec airflow_webserver airflow dags test actualizar_lotes_caducados 2024-01-12`

## 📚 Referencias

- [Apache Airflow Documentation](https://airflow.apache.org/docs/)
- [Airflow Operators](https://airflow.apache.org/docs/apache-airflow/stable/operators.html)
- [Celery Executor](https://airflow.apache.org/docs/apache-airflow/stable/executor/celery.html)
- [Telegram Bot API](https://core.telegram.org/bots/api)

---

**Última actualización**: 2024-01-12
**Versión**: 1.0
