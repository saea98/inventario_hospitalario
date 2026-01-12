# ⚡ Inicio Rápido - Airflow

## 1️⃣ Configurar Base de Datos (2 min)

Edita el archivo `.env`:

```bash
nano .env
```

Actualiza estos valores con tu BD existente:

```env
# POSTGRESQL - INVENTARIO HOSPITALARIO
DB_HOST=localhost              # o tu IP/hostname
DB_PORT=5432                   # puerto de tu PostgreSQL
DB_NAME=inventario_hospitalario
DB_USER=postgres               # usuario de tu BD
DB_PASSWORD=tu_contraseña      # contraseña de tu BD
```

## 2️⃣ Obtener Token de Telegram (Opcional - 5 min)

### Crear Bot de Telegram
1. Abre Telegram → Busca **@BotFather**
2. Envía `/newbot`
3. Sigue instrucciones → Copia el **TOKEN**

### Obtener Chat ID
1. Abre Telegram → Busca **@userinfobot**
2. Envía `/start` → Copia tu **User ID**

### Configurar en .env

```env
TELEGRAM_BOT_TOKEN=tu_token_aqui
TELEGRAM_CHAT_ID=tu_chat_id_aqui
```

## 3️⃣ Iniciar Airflow (3 min)

```bash
# Crear directorios
mkdir -p dags logs plugins config

# Iniciar contenedores
docker-compose up -d

# Esperar 30 segundos
sleep 30

# Configurar automáticamente
bash init_airflow.sh
```

## 4️⃣ Acceder a Airflow (1 min)

- **URL**: http://localhost:8080
- **Usuario**: admin
- **Contraseña**: admin

## 5️⃣ Activar el DAG (1 min)

1. Busca **"actualizar_lotes_caducados"**
2. Haz clic en el **toggle** para activarlo
3. ¡Listo! Se ejecutará diariamente a las 2:00 AM

## ✅ Verificar que Funciona

```bash
# Ver estado de contenedores
docker-compose ps

# Ver logs
docker-compose logs -f airflow-webserver

# Ejecutar DAG manualmente
docker exec airflow_webserver airflow dags test actualizar_lotes_caducados 2024-01-12
```

## 🔗 Enlaces Útiles

| Servicio | URL |
|----------|-----|
| Airflow | http://localhost:8080 |
| Flower (Monitor) | http://localhost:5555 |

## 🆘 Problemas Comunes

**"No se puede conectar a PostgreSQL"**
```bash
# Verificar conectividad desde el contenedor
docker exec airflow_webserver psql -h <DB_HOST> -U <DB_USER> -d <DB_NAME> -c "SELECT 1"

# Ejemplo:
docker exec airflow_webserver psql -h localhost -U postgres -d inventario_hospitalario -c "SELECT 1"
```

**"Telegram no envía mensajes"**
```bash
# Verificar token
docker exec airflow_webserver airflow variables get TELEGRAM_BOT_TOKEN

# Probar conexión
curl -X GET "https://api.telegram.org/botTOKEN/getMe"
```

**"El DAG no aparece"**
```bash
# Recargar DAGs
docker exec airflow_webserver airflow dags reserialize

# Reiniciar scheduler
docker-compose restart airflow-scheduler
```

---

**¿Necesitas más ayuda?** Ver `README.md` para documentación completa.
