# 📋 Resumen Ejecutivo - DAG Airflow para Lotes Caducados

## ¿Qué es?

Sistema automatizado que **revisa diariamente los lotes caducados** en tu inventario hospitalario y los marca como **no disponibles** automáticamente. Incluye notificaciones por Telegram y un panel de control web.

## ✨ Características Principales

| Característica | Descripción |
|---|---|
| **Ejecución Automática** | Diariamente a las 2:00 AM |
| **Identificación de Caducados** | Busca lotes con fecha de caducidad vencida |
| **Actualización Automática** | Marca como no disponible y caducado |
| **Auditoría** | Registra todos los cambios |
| **Notificaciones** | Envía resumen por Telegram |
| **Panel Web** | Monitorea ejecuciones en tiempo real |
| **Monitor de Tareas** | Flower para ver estado de workers |

## 📦 Archivos Creados

```
airflow_setup/
├── dags/
│   └── actualizar_lotes_caducados.py    ← DAG principal
├── docker-compose.yml                    ← Orquestación
├── Dockerfile                            ← Imagen personalizada
├── requirements.txt                      ← Dependencias Python
├── .env                                  ← Variables de entorno
├── config/
│   └── airflow.cfg                       ← Configuración
├── init_airflow.sh                       ← Inicialización automática
├── configure_airflow.py                  ← Configurador interactivo
├── health_check.sh                       ← Verificación de salud
├── cleanup.sh                            ← Limpieza
├── README.md                             ← Documentación completa
├── QUICKSTART.md                         ← Inicio rápido
└── RESUMEN.md                            ← Este archivo
```

## 🚀 Inicio Rápido (5 minutos)

### 1. Obtener Token de Telegram (Opcional)

```bash
# En Telegram:
# 1. Busca @BotFather
# 2. Envía /newbot
# 3. Copia el TOKEN que te da
```

### 2. Configurar Variables

```bash
cd ~/inventario_hospitalario/airflow_setup
nano .env

# Edita:
TELEGRAM_BOT_TOKEN=tu_token_aqui
TELEGRAM_CHAT_ID=tu_chat_id_aqui
DB_PASSWORD=tu_contraseña_postgres
```

### 3. Iniciar

```bash
mkdir -p dags logs plugins config
docker-compose up -d
sleep 30
bash init_airflow.sh
```

### 4. Acceder

- **Airflow**: http://localhost:8080 (admin/admin)
- **Flower**: http://localhost:5555

### 5. Activar DAG

1. En Airflow Web, busca "actualizar_lotes_caducados"
2. Haz clic en el toggle para activarlo
3. ¡Listo! Se ejecutará diariamente a las 2:00 AM

## 🔄 Cómo Funciona

```
┌─────────────────────────────────────────────────────────┐
│ Diariamente a las 2:00 AM                               │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 1. Obtener Lotes Caducados                              │
│    - Conecta a PostgreSQL                               │
│    - Busca lotes con fecha_caducidad < HOY              │
│    - Filtra los no marcados como caducados              │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 2. Actualizar Lotes                                     │
│    - Marca disponible = false                           │
│    - Cambia estado = 'caducado'                         │
│    - Registra en auditoría                              │
└─────────────────────────────────────────────────────────┘
                        ↓
        ┌───────────────┴───────────────┐
        ↓                               ↓
┌──────────────────┐        ┌──────────────────┐
│ 3. Notificación  │        │ 4. Registrar     │
│    por Telegram  │        │    Resumen       │
│    (Opcional)    │        │                  │
└──────────────────┘        └──────────────────┘
```

## 📊 Interfaz Web

### Airflow (http://localhost:8080)

- **DAGs**: Ver todos los DAGs disponibles
- **Ejecuciones**: Historial de ejecuciones
- **Logs**: Ver logs detallados de cada tarea
- **Variables**: Gestionar variables de configuración
- **Conexiones**: Gestionar conexiones a BD

### Flower (http://localhost:5555)

- **Workers**: Estado de workers
- **Tareas**: Tareas en cola y completadas
- **Estadísticas**: Gráficos de rendimiento

## 🔧 Configuración

### Variables de Airflow

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `DB_HOST` | Host de PostgreSQL | `host.docker.internal` |
| `DB_PORT` | Puerto de PostgreSQL | `5432` |
| `DB_NAME` | Nombre de BD | `inventario_hospitalario` |
| `DB_USER` | Usuario de BD | `postgres` |
| `DB_PASSWORD` | Contraseña de BD | `tu_contraseña` |
| `TELEGRAM_BOT_TOKEN` | Token del bot | `123456:ABC-DEF...` |
| `TELEGRAM_CHAT_ID` | Chat ID | `987654321` |

### Cambiar Horario de Ejecución

Edita `dags/actualizar_lotes_caducados.py` línea 35:

```python
schedule_interval='0 2 * * *',  # Formato: HH MM * * *
```

Ejemplos:
- `'0 0 * * *'` → Medianoche
- `'0 */6 * * *'` → Cada 6 horas
- `'0 0 * * 1'` → Lunes a medianoche

## 🆘 Troubleshooting

### "No se puede conectar a PostgreSQL"

```bash
# Verificar conectividad
docker exec airflow_webserver psql -h host.docker.internal -U postgres -d inventario_hospitalario -c "SELECT 1"

# Si falla, edita .env:
# - En Docker Desktop: host.docker.internal
# - En Linux: IP de la red Docker o nombre del contenedor
```

### "Telegram no envía mensajes"

```bash
# Verificar token
docker exec airflow_webserver airflow variables get TELEGRAM_BOT_TOKEN

# Probar conexión
curl -X GET "https://api.telegram.org/botTOKEN/getMe"
```

### "El DAG no aparece"

```bash
# Recargar DAGs
docker exec airflow_webserver airflow dags reserialize

# Reiniciar scheduler
docker-compose restart airflow-scheduler
```

## 🧹 Limpieza

```bash
# Detener y eliminar todo
bash cleanup.sh

# Reiniciar desde cero
docker-compose up -d
bash init_airflow.sh
```

## ✅ Verificación

```bash
# Verificar salud del sistema
bash health_check.sh

# Ver estado de contenedores
docker-compose ps

# Ver logs
docker-compose logs -f airflow-webserver
```

## 📞 Soporte

1. **Documentación Completa**: Ver `README.md`
2. **Inicio Rápido**: Ver `QUICKSTART.md`
3. **Verificación**: Ejecutar `bash health_check.sh`

## 🎯 Próximos Pasos

1. ✅ Configurar variables en `.env`
2. ✅ Iniciar Airflow con `docker-compose up -d`
3. ✅ Ejecutar `bash init_airflow.sh`
4. ✅ Acceder a http://localhost:8080
5. ✅ Activar el DAG
6. ✅ Monitorear en Airflow Web y Flower

## 📈 Beneficios

| Beneficio | Descripción |
|-----------|-------------|
| **Automatización** | Sin intervención manual |
| **Confiabilidad** | Reintentos automáticos |
| **Trazabilidad** | Registro de todos los cambios |
| **Notificaciones** | Alertas en tiempo real |
| **Monitoreo** | Panel web completo |
| **Escalabilidad** | Fácil de extender |

---

**Versión**: 1.0  
**Fecha**: 2024-01-12  
**Autor**: Sistema de Inventario Hospitalario
