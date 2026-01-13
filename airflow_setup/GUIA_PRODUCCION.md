# 🚀 Guía de Instalación - Airflow para Inventario Hospitalario

**Versión**: 1.0  
**Fecha**: 2026-01-12  
**Destinatario**: Equipo de Producción

---

## 📋 Requisitos Previos

Antes de comenzar, asegúrate de tener:

- ✅ **Docker** instalado (versión 20.10 o superior)
- ✅ **Docker Compose** instalado (versión 1.29 o superior)
- ✅ **Git** instalado
- ✅ **Acceso al repositorio** del proyecto
- ✅ **Base de datos PostgreSQL existente** del inventario hospitalario
- ✅ **Credenciales de acceso** a la BD
- ✅ **Token de Telegram** (opcional, para notificaciones)

### Verificar Instalaciones

```bash
# Verificar Docker
docker --version

# Verificar Docker Compose
docker-compose --version

# Verificar Git
git --version
```

---

## 🔧 Paso 1: Clonar el Repositorio

```bash
# Ir a la carpeta donde deseas instalar
cd /opt  # o la ruta que prefieras

# Clonar el repositorio
git clone https://github.com/saea98/inventario_hospitalario.git

# Entrar a la carpeta de Airflow
cd inventario_hospitalario/airflow_setup
```

---

## ⚙️ Paso 2: Configurar Variables de Entorno

### 2.1 Editar el archivo `.env`

```bash
nano .env
```

### 2.2 Configurar Parámetros de Base de Datos

Reemplaza los valores con los de tu servidor:

```env
# ============================================
# CONFIGURACIÓN DE AIRFLOW
# ============================================
AIRFLOW_UID=50000
AIRFLOW_GID=50000
AIRFLOW_PROJ_DIR=.

# ============================================
# POSTGRESQL - AIRFLOW METADATA
# ============================================
AIRFLOW_DB_USER=airflow
AIRFLOW_DB_PASSWORD=airflow
AIRFLOW_DB_NAME=airflow

# ============================================
# USUARIO ADMIN DE AIRFLOW
# ============================================
_AIRFLOW_WWW_USER_USERNAME=admin
_AIRFLOW_WWW_USER_PASSWORD=CAMBIAR_CONTRASEÑA_AQUI

# ============================================
# POSTGRESQL - INVENTARIO HOSPITALARIO
# ============================================
DB_HOST=192.168.1.100              # IP o hostname de tu servidor PostgreSQL
DB_PORT=5432                        # Puerto de PostgreSQL
DB_NAME=inventario_bd               # Nombre de la BD
DB_USER=postgres                    # Usuario de BD
DB_PASSWORD=tu_contraseña_aqui      # Contraseña de BD

# ============================================
# TELEGRAM - NOTIFICACIONES (OPCIONAL)
# ============================================
TELEGRAM_BOT_TOKEN=                 # Dejar vacío si no usas Telegram
TELEGRAM_CHAT_ID=                   # Dejar vacío si no usas Telegram
```

**⚠️ IMPORTANTE**: Cambiar las contraseñas por valores seguros.

### 2.3 Obtener Token de Telegram (Opcional)

Si deseas recibir notificaciones por Telegram:

1. **Crear Bot**:
   - Abre Telegram
   - Busca `@BotFather`
   - Envía `/newbot`
   - Sigue las instrucciones
   - Copia el TOKEN que te da

2. **Obtener Chat ID**:
   - Busca `@userinfobot`
   - Envía `/start`
   - Copia tu User ID

3. **Actualizar `.env`**:
   ```env
   TELEGRAM_BOT_TOKEN=123456:ABC-DEF-GHI-JKL
   TELEGRAM_CHAT_ID=987654321
   ```

---

## 🐳 Paso 3: Iniciar Airflow

### 3.1 Crear Directorios Necesarios

```bash
mkdir -p dags logs plugins config
```

### 3.2 Iniciar los Contenedores

```bash
# Aumentar timeout para descargar imágenes
COMPOSE_HTTP_TIMEOUT=300 docker-compose up -d

# Esperar 2-3 minutos a que todo inicie
sleep 180
```

### 3.3 Verificar Estado de los Contenedores

```bash
docker-compose ps
```

**Esperado**: Todos los contenedores deben estar en estado `Up`

```
NAME                COMMAND                  STATE
postgres_airflow    docker-entrypoint.sh     Up (healthy)
airflow_webserver   /usr/bin/dumb-init       Up (healthy)
airflow_scheduler   /usr/bin/dumb-init       Up
```

---

## 🔐 Paso 4: Acceder a Airflow

### 4.1 Abrir en el Navegador

```
http://localhost:8080
```

O si es en un servidor remoto:

```
http://IP_DEL_SERVIDOR:8080
```

### 4.2 Credenciales de Acceso

- **Usuario**: `admin`
- **Contraseña**: La que configuraste en `.env` (`_AIRFLOW_WWW_USER_PASSWORD`)

### 4.3 Cambiar Contraseña (Recomendado)

1. Haz clic en el icono de usuario (arriba a la derecha)
2. Selecciona "Change Password"
3. Ingresa la contraseña actual y la nueva

---

## ✅ Paso 5: Activar el DAG

### 5.1 Buscar el DAG

1. En Airflow Web, ve a la sección **DAGs**
2. Busca `actualizar_lotes_caducados`

### 5.2 Activar el DAG

1. Haz clic en el **toggle** (switch) para activarlo
2. El DAG se ejecutará automáticamente **diariamente a las 2:00 AM**

### 5.3 Probar Manualmente (Opcional)

Para verificar que funciona:

```bash
# Ejecutar el DAG manualmente
docker exec airflow_webserver airflow dags test actualizar_lotes_caducados 2024-01-12
```

---

## 📊 Paso 6: Monitoreo

### 6.1 Panel de Control

- **Airflow Web**: http://localhost:8080
  - Ver DAGs
  - Monitorear ejecuciones
  - Ver logs

### 6.2 Ver Logs en Tiempo Real

```bash
# Logs del webserver
docker-compose logs -f airflow_webserver

# Logs del scheduler
docker-compose logs -f airflow_scheduler

# Todos los logs
docker-compose logs -f
```

### 6.3 Ver Estado de Contenedores

```bash
docker-compose ps
```

---

## 🔍 Troubleshooting

### Problema: "No se puede conectar a PostgreSQL"

**Solución**:

```bash
# Verificar conectividad desde el contenedor
docker exec airflow_webserver psql -h DB_HOST -U DB_USER -d DB_NAME -c "SELECT 1"

# Ejemplo:
docker exec airflow_webserver psql -h 192.168.1.100 -U postgres -d inventario_bd -c "SELECT 1"
```

Si falla:
- Verificar que la IP/hostname es correcta
- Verificar que el puerto es correcto (por defecto 5432)
- Verificar credenciales de usuario y contraseña
- Verificar que el firewall permite la conexión

### Problema: "El DAG no aparece"

**Solución**:

```bash
# Recargar DAGs
docker exec airflow_webserver airflow dags reserialize

# Reiniciar scheduler
docker-compose restart airflow_scheduler

# Esperar 30 segundos y verificar
sleep 30
docker-compose ps
```

### Problema: "Los contenedores se cierran"

**Solución**:

```bash
# Ver logs de error
docker logs airflow_webserver

# Detener y limpiar
docker-compose down -v

# Reiniciar
COMPOSE_HTTP_TIMEOUT=300 docker-compose up -d
```

### Problema: "Telegram no envía mensajes"

**Solución**:

```bash
# Verificar que las variables están configuradas
docker exec airflow_webserver airflow variables list | grep TELEGRAM

# Probar conexión a Telegram
curl -X GET "https://api.telegram.org/botTOKEN/getMe"
```

---

## 🛑 Detener Airflow

```bash
# Detener contenedores (sin eliminar datos)
docker-compose down

# Detener y eliminar todo (CUIDADO: elimina datos)
docker-compose down -v
```

---

## 📈 Información del DAG

### ¿Qué hace?

El DAG `actualizar_lotes_caducados` realiza las siguientes acciones **diariamente a las 2:00 AM**:

1. **Conecta** a la base de datos del inventario
2. **Identifica** lotes con fecha de caducidad vencida
3. **Marca** los lotes como:
   - `estado = 6` (caducado)
   - `cantidad_disponible = 0` (no disponible)
4. **Registra** el cambio en `motivo_cambio_estado`
5. **Envía** notificación por Telegram (si está configurado)

### Estados de Lotes

| Estado | Significado |
|--------|-------------|
| 1 | Disponible |
| 6 | Caducado |

### Cambiar Horario de Ejecución

Si necesitas cambiar la hora de ejecución:

```bash
# Editar el DAG
nano dags/actualizar_lotes_caducados.py

# Buscar la línea:
# schedule_interval='0 2 * * *',

# Cambiar los números:
# Formato: HH MM * * *
# Ejemplos:
# '0 0 * * *'  → Medianoche
# '0 12 * * *' → Mediodía
# '0 */6 * * *' → Cada 6 horas
```

Después reiniciar:

```bash
docker exec airflow_webserver airflow dags reserialize
docker-compose restart airflow_scheduler
```

---

## 📞 Soporte

En caso de problemas:

1. **Ver logs**: `docker-compose logs -f`
2. **Verificar conectividad**: `docker exec airflow_webserver psql -h DB_HOST -U DB_USER -d DB_NAME -c "SELECT 1"`
3. **Reiniciar**: `docker-compose restart`
4. **Contactar al equipo de desarrollo**

---

## ✨ Checklist de Instalación

- [ ] Docker y Docker Compose instalados
- [ ] Repositorio clonado
- [ ] Archivo `.env` configurado
- [ ] Credenciales de BD verificadas
- [ ] Contenedores iniciados correctamente
- [ ] Acceso a Airflow Web confirmado
- [ ] DAG `actualizar_lotes_caducados` activado
- [ ] Prueba manual del DAG exitosa
- [ ] Notificaciones de Telegram configuradas (opcional)

---

**¡Listo! Airflow está en producción y funcionando.**

Para más información, consulta la documentación en `README.md`.
