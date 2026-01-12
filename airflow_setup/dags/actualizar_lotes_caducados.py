"""
DAG para revisar y actualizar lotes caducados en el inventario hospitalario.

Este DAG se ejecuta diariamente y:
1. Conecta a la base de datos PostgreSQL del inventario
2. Identifica lotes con fecha de caducidad vencida
3. Marca los lotes como caducados y no disponibles
4. Registra los cambios en la BD de Airflow
5. Envía notificación por Telegram
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.models import Variable
from airflow.exceptions import AirflowException
import psycopg2
from psycopg2.extras import RealDictCursor
import requests
import logging
from typing import List, Dict

# Configuración de logging
logger = logging.getLogger(__name__)

# Argumentos por defecto del DAG
default_args = {
    'owner': 'inventario-hospitalario',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'email_on_failure': False,
    'email_on_retry': False,
}

# Definición del DAG
dag = DAG(
    'actualizar_lotes_caducados',
    default_args=default_args,
    description='Revisa y actualiza lotes caducados en el inventario',
    schedule_interval='0 2 * * *',  # Diariamente a las 2:00 AM
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['inventario', 'lotes', 'mantenimiento'],
)


def obtener_credenciales_db():
    """
    Obtiene credenciales de BD desde variables de Airflow.
    """
    try:
        # En Airflow 2.10.2, usar deserialize_json=False y manejar excepciones
        try:
            db_host = Variable.get("DB_HOST", deserialize_json=False)
        except KeyError:
            db_host = "localhost"
        
        try:
            db_port = Variable.get("DB_PORT", deserialize_json=False)
        except KeyError:
            db_port = "5432"
        
        try:
            db_name = Variable.get("DB_NAME", deserialize_json=False)
        except KeyError:
            db_name = "inventario_hospitalario"
        
        try:
            db_user = Variable.get("DB_USER", deserialize_json=False)
        except KeyError:
            db_user = "postgres"
        
        try:
            db_password = Variable.get("DB_PASSWORD", deserialize_json=False)
        except KeyError:
            db_password = ""
        
        logger.info(f"Conectando a {db_host}:{db_port}/{db_name}")
        
        return {
            'host': db_host,
            'port': db_port,
            'database': db_name,
            'user': db_user,
            'password': db_password
        }
    except Exception as e:
        logger.error(f"Error obteniendo credenciales: {str(e)}")
        raise AirflowException(f"No se pudieron obtener credenciales de BD: {str(e)}")


def obtener_conexion_db():
    """Obtiene conexión a la base de datos PostgreSQL."""
    try:
        creds = obtener_credenciales_db()
        conn = psycopg2.connect(**creds)
        return conn
    except Exception as e:
        logger.error(f"Error conectando a la base de datos: {str(e)}")
        raise AirflowException(f"No se pudo conectar a la BD: {str(e)}")


def obtener_lotes_caducados(**context):
    """
    Obtiene los lotes que están caducados.
    
    Returns:
        Dict con información de lotes caducados
    """
    try:
        conn = obtener_conexion_db()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Query para obtener lotes caducados que no estén ya marcados como caducados
        query = """
            SELECT 
                l.id,
                l.numero_lote,
                l.fecha_caducidad,
                l.disponible,
                l.estado,
                p.nombre as producto_nombre,
                p.clave as producto_clave
            FROM inventario_lote l
            JOIN inventario_producto p ON l.producto_id = p.id
            WHERE 
                l.fecha_caducidad < CURRENT_DATE
                AND l.disponible = true
                AND l.estado != 'caducado'
            ORDER BY l.fecha_caducidad ASC
        """
        
        cursor.execute(query)
        lotes_caducados = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        logger.info(f"Se encontraron {len(lotes_caducados)} lotes caducados")
        
        # Pasar información al siguiente task
        context['task_instance'].xcom_push(
            key='lotes_caducados',
            value=[dict(row) for row in lotes_caducados]
        )
        
        return {
            'cantidad_lotes': len(lotes_caducados),
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo lotes caducados: {str(e)}")
        raise AirflowException(f"Error en obtener_lotes_caducados: {str(e)}")


def actualizar_lotes_caducados(**context):
    """
    Marca los lotes caducados como no disponibles y actualiza su estado.
    """
    try:
        # Obtener lotes del task anterior
        lotes_caducados = context['task_instance'].xcom_pull(
            task_ids='obtener_lotes_caducados',
            key='lotes_caducados'
        )
        
        if not lotes_caducados:
            logger.info("No hay lotes caducados para actualizar")
            context['task_instance'].xcom_push(
                key='lotes_actualizados',
                value=[]
            )
            return {'cantidad_actualizados': 0}
        
        conn = obtener_conexion_db()
        cursor = conn.cursor()
        
        lotes_actualizados = []
        
        for lote in lotes_caducados:
            try:
                # Actualizar el lote
                update_query = """
                    UPDATE inventario_lote
                    SET 
                        disponible = false,
                        estado = 'caducado',
                        fecha_actualizacion = CURRENT_TIMESTAMP
                    WHERE id = %s
                """
                
                cursor.execute(update_query, (lote['id'],))
                
                # Registrar el cambio en la tabla de auditoría si existe
                try:
                    audit_query = """
                        INSERT INTO inventario_auditorialote 
                        (lote_id, accion, descripcion, fecha_cambio)
                        VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                    """
                    
                    descripcion = f"Lote marcado como caducado automáticamente. Fecha caducidad: {lote['fecha_caducidad']}"
                    cursor.execute(audit_query, (lote['id'], 'CADUCADO', descripcion))
                except Exception as e:
                    logger.warning(f"No se pudo registrar en auditoría: {str(e)}")
                
                lotes_actualizados.append({
                    'id': lote['id'],
                    'numero_lote': lote['numero_lote'],
                    'producto': lote['producto_nombre'],
                    'clave': lote['producto_clave'],
                    'fecha_caducidad': str(lote['fecha_caducidad'])
                })
                
                logger.info(f"Lote {lote['numero_lote']} marcado como caducado")
                
            except Exception as e:
                logger.error(f"Error actualizando lote {lote['id']}: {str(e)}")
                conn.rollback()
                continue
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"Se actualizaron {len(lotes_actualizados)} lotes")
        
        # Pasar información al siguiente task
        context['task_instance'].xcom_push(
            key='lotes_actualizados',
            value=lotes_actualizados
        )
        
        return {'cantidad_actualizados': len(lotes_actualizados)}
        
    except Exception as e:
        logger.error(f"Error actualizando lotes caducados: {str(e)}")
        raise AirflowException(f"Error en actualizar_lotes_caducados: {str(e)}")


def enviar_notificacion_telegram(**context):
    """
    Envía notificación por Telegram con el resumen de lotes caducados.
    """
    try:
        # Obtener variables de Telegram
        try:
            telegram_token = Variable.get("TELEGRAM_BOT_TOKEN", deserialize_json=False)
        except KeyError:
            telegram_token = ""
        
        try:
            telegram_chat_id = Variable.get("TELEGRAM_CHAT_ID", deserialize_json=False)
        except KeyError:
            telegram_chat_id = ""
        
        if not telegram_token or not telegram_chat_id:
            logger.warning("Variables de Telegram no configuradas, saltando notificación")
            logger.info(f"Token: {bool(telegram_token)}, Chat ID: {bool(telegram_chat_id)}")
            return
        
        # Obtener lotes actualizados
        lotes_actualizados = context['task_instance'].xcom_pull(
            task_ids='actualizar_lotes_caducados',
            key='lotes_actualizados'
        )
        
        if not lotes_actualizados:
            logger.info("No hay lotes para notificar")
            return
        
        # Construir mensaje
        mensaje = "🚨 *Reporte de Lotes Caducados*\n\n"
        mensaje += f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        mensaje += f"📦 Total de lotes caducados: {len(lotes_actualizados)}\n\n"
        
        mensaje += "*Lotes Procesados:*\n"
        for lote in lotes_actualizados[:10]:  # Mostrar máximo 10 en el mensaje
            mensaje += f"• {lote['numero_lote']} - {lote['producto']} (Clave: {lote['clave']})\n"
            mensaje += f"  Caducidad: {lote['fecha_caducidad']}\n"
        
        if len(lotes_actualizados) > 10:
            mensaje += f"\n... y {len(lotes_actualizados) - 10} lotes más\n"
        
        mensaje += "\n✅ Los lotes han sido marcados como no disponibles"
        
        # Enviar por Telegram
        url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
        payload = {
            'chat_id': telegram_chat_id,
            'text': mensaje,
            'parse_mode': 'Markdown'
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            logger.info("Notificación enviada por Telegram exitosamente")
        else:
            logger.error(f"Error enviando notificación por Telegram: {response.text}")
            raise AirflowException(f"Error en Telegram: {response.text}")
        
    except Exception as e:
        logger.error(f"Error en enviar_notificacion_telegram: {str(e)}")
        # No lanzar excepción para que el DAG no falle si Telegram falla
        logger.warning("Continuando a pesar del error en Telegram")


def registrar_resumen(**context):
    """
    Registra un resumen de la ejecución del DAG.
    """
    try:
        cantidad_lotes = context['task_instance'].xcom_pull(
            task_ids='actualizar_lotes_caducados',
            key='lotes_actualizados'
        )
        
        resumen = {
            'fecha_ejecucion': datetime.now().isoformat(),
            'cantidad_lotes_procesados': len(cantidad_lotes) if cantidad_lotes else 0,
            'estado': 'exitoso'
        }
        
        logger.info(f"Resumen de ejecución: {resumen}")
        
        return resumen
        
    except Exception as e:
        logger.error(f"Error registrando resumen: {str(e)}")
        raise AirflowException(f"Error en registrar_resumen: {str(e)}")


# Definición de tareas
tarea_obtener = PythonOperator(
    task_id='obtener_lotes_caducados',
    python_callable=obtener_lotes_caducados,
    provide_context=True,
    dag=dag,
)

tarea_actualizar = PythonOperator(
    task_id='actualizar_lotes_caducados',
    python_callable=actualizar_lotes_caducados,
    provide_context=True,
    dag=dag,
)

tarea_notificar = PythonOperator(
    task_id='enviar_notificacion_telegram',
    python_callable=enviar_notificacion_telegram,
    provide_context=True,
    dag=dag,
)

tarea_resumen = PythonOperator(
    task_id='registrar_resumen',
    python_callable=registrar_resumen,
    provide_context=True,
    dag=dag,
)

# Definir orden de ejecución
tarea_obtener >> tarea_actualizar >> [tarea_notificar, tarea_resumen]
