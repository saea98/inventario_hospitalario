# dags/sicop_carga_operacion_robusto.py
from datetime import datetime, timedelta
import requests
import base64
import time
import os
import xml.etree.ElementTree as ET
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.models import Variable
from airflow.exceptions import AirflowException
import logging
import urllib3
import sys

# Configuración para logs más limpios
sys.tracebacklimit = 0

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

default_args = {
    'owner': 'sicop_team',
    'depends_on_past': False,
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 0,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(hours=2),
}

class SICOPException(AirflowException):
    """Excepción personalizada para errores de SICOP"""
    pass

class SICOPValidationException(SICOPException):
    """Excepción para errores de validación de datos"""
    pass

class SICOPClient:
    """Cliente robusto para integración con SICOP"""
    
    @staticmethod
    def get_config():
        return {
            'usuario': Variable.get("SICOP_USUARIO", default_var="tuusuario"),
            'password': Variable.get("SICOP_PASSWORD", default_var="tupassword"),
            'ambiente': Variable.get("SICOP_AMBIENTE", default_var="calidad"),
            'archivo_path': Variable.get("SICOP_ARCHIVO_PATH", default_var="/opt/airflow/data/sicop/carga.zip"),
            'ramo': Variable.get("SICOP_RAMO", default_var="52"),
            'instancia': Variable.get("SICOP_INSTANCIA", default_var="SICOP25"),
            'flujo': Variable.get("SICOP_FLUJO", default_var="EE_PRESUPUESTO"),
            'documento': Variable.get("SICOP_DOCUMENTO", default_var="DOC_EEP"),
            'intervalo': int(Variable.get("SICOP_INTERVALO_CONSULTA", default_var=60)),
            'max_intentos': int(Variable.get("SICOP_MAX_INTENTOS", default_var=60)),
        }
    
    @staticmethod
    def get_auth_header(usuario, password):
        if not usuario or not password:
            raise AirflowException("Credenciales SICOP no configuradas")
        credentials = f"{usuario}:{password}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return {"AuthSHCP": encoded}
    
    @staticmethod
    def get_endpoint_url(ambiente, ramo):
        base_url = "https://pruebas-sicopep.hacienda.gob.mx" if ambiente == "calidad" \
                  else "https://sicopep.hacienda.gob.mx"
        return f"{base_url}/sicop{ramo}/services/CargaOperacion"
    
    @staticmethod
    def parse_soap_fault(response_text):
        try:
            root = ET.fromstring(response_text)
            fault_code = root.find('.//{*}faultcode')
            fault_string = root.find('.//{*}faultstring')
            
            if fault_code is not None and fault_string is not None:
                message = fault_string.text or ""
                return {
                    'code': fault_code.text,
                    'message': message,
                    'is_validation_error': 'Error al generar archivo XML de carga' in message or 
                                          'Error al intentar registrar documento' in message
                }
            return None
        except:
            return None
    
    @staticmethod
    def parse_status_response(response_text):
        try:
            root = ET.fromstring(response_text)
            string_elements = root.findall('.//{*}string')
            
            if not string_elements:
                return None
            
            estado = string_elements[0].text.strip() if string_elements[0].text else None
            
            errores = []
            if len(string_elements) > 1:
                for elem in string_elements[1:]:
                    if elem.text and elem.text.strip():
                        errores.append(elem.text.strip())
            
            return {
                'estado': estado,
                'errores': errores
            }
        except:
            return None

def log_separador():
    """Línea separadora visual"""
    logger.info("=" * 80)

def log_titulo(texto, simbolo="📌"):
    """Título destacado"""
    logger.info("")
    log_separador()
    logger.info(f"{simbolo} {texto}")
    log_separador()

def log_subtitulo(texto):
    """Subtítulo"""
    logger.info("")
    logger.info(f"▶ {texto}")
    logger.info("-" * 80)

def log_dato(clave, valor):
    """Par clave-valor"""
    logger.info(f"  • {clave}: {valor}")

def log_xml_formateado(titulo, xml_text):
    """Muestra XML formateado y legible"""
    log_titulo(titulo, "📄")
    
    try:
        # Intentar formatear
        root = ET.fromstring(xml_text)
        ET.indent(root, space="  ")
        formatted = ET.tostring(root, encoding='unicode')
        
        for line in formatted.split('\n'):
            if line.strip():
                logger.info(f"  {line}")
    except:
        # Si falla, mostrar raw
        for line in xml_text.split('\n'):
            if line.strip():
                logger.info(f"  {line.strip()}")
    
    log_separador()
    logger.info("")

def extraer_ticket_de_xml(xml_text):
    """Intenta extraer el ticket del XML por todos los medios"""
    try:
        root = ET.fromstring(xml_text)
        
        # Buscar en <return>
        for elem in root.iter():
            if 'return' in elem.tag.lower() and elem.text:
                return elem.text.strip()
        
        # Buscar cualquier elemento que parezca un ticket (número)
        for elem in root.iter():
            if elem.text and elem.text.strip().isdigit():
                return elem.text.strip()
        
        return None
    except:
        return None

def validar_configuracion(**context):
    """Valida configuración antes de ejecutar"""
    log_titulo("VALIDACIÓN DE CONFIGURACIÓN", "🔍")
    
    config = SICOPClient.get_config()
    
    if not config['usuario'] or not config['password']:
        logger.error("")
        logger.error("❌ ERROR: Credenciales no configuradas")
        logger.error("  Configura SICOP_USUARIO y SICOP_PASSWORD en Airflow Variables")
        logger.error("")
        raise AirflowException("Credenciales no configuradas")
    
    if not os.path.exists(config['archivo_path']):
        logger.error("")
        logger.error(f"❌ ERROR: Archivo no encontrado")
        logger.error(f"  Ruta: {config['archivo_path']}")
        logger.error("")
        raise AirflowException(f"Archivo no encontrado: {config['archivo_path']}")
    
    file_size = os.path.getsize(config['archivo_path'])
    if file_size == 0:
        logger.error("")
        logger.error("❌ ERROR: Archivo vacío (0 bytes)")
        logger.error("")
        raise AirflowException("Archivo vacío")
    
    logger.info("")
    logger.info("✅ Configuración válida:")
    log_dato("Archivo", config['archivo_path'])
    log_dato("Tamaño", f"{file_size/1024:.2f} KB")
    log_dato("Instancia", config['instancia'])
    log_dato("Flujo", config['flujo'])
    log_dato("Documento", config['documento'])
    log_dato("Ambiente", config['ambiente'].upper())
    logger.info("")
    
    return config

def cargar_archivo_sicop(**context):
    """Envía el archivo a SICOP y recibe el TICKET"""
    ti = context['ti']
    config = ti.xcom_pull(task_ids='validar_configuracion')
    
    log_titulo("CARGA DE ARCHIVO A SICOP", "📤")
    
    # Preparar archivo
    logger.info("Leyendo y codificando archivo...")
    with open(config['archivo_path'], 'rb') as f:
        file_content = f.read()
    
    encoded_content = base64.b64encode(file_content).decode('utf-8')
    log_dato("Archivo codificado", f"{len(encoded_content)} caracteres")
    
    # SOAP request
    soap_payload = f"""<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ser="http://service.cargaoperacion.sicop.shcp.gob.mx/">
  <soapenv:Header/>
  <soapenv:Body>
    <ser:carga>
      <in0>{config['instancia']}</in0>
      <in1>{config['flujo']}</in1>
      <in2>{config['documento']}</in2>
      <in3>{encoded_content}</in3>
    </ser:carga>
  </soapenv:Body>
</soapenv:Envelope>"""
    
    headers = {
        'Content-Type': 'text/xml; charset=utf-8',
        'SOAPAction': 'carga',
        'User-Agent': 'Airflow-SICOP/2.10.2'
    }
    headers.update(SICOPClient.get_auth_header(config['usuario'], config['password']))
    
    url = SICOPClient.get_endpoint_url(config['ambiente'], config['ramo'])
    
    log_subtitulo("Enviando petición SOAP")
    log_dato("URL", url)
    log_dato("Instancia", config['instancia'])
    
    # Enviar
    response = requests.post(
        url, 
        params={'instancia': config['instancia']},
        data=soap_payload, 
        headers=headers, 
        timeout=300,
        verify=False
    )
    
    log_dato("HTTP Status", response.status_code)
    logger.info("")
    
    # SIEMPRE MOSTRAR EL XML COMPLETO
    log_xml_formateado("RESPONSE XML COMPLETO", response.text)
    
    # Guardar XML en XCom
    ti.xcom_push(key='response_xml_carga', value=response.text)
    
    # INTENTAR EXTRAER TICKET PRIMERO (antes de verificar errores)
    ticket_encontrado = extraer_ticket_de_xml(response.text)
    
    if ticket_encontrado:
        logger.info("")
        logger.info("🎫" * 40)
        logger.info("🎫" * 40)
        logger.info("")
        logger.info(f"           ✅ TICKET RECIBIDO: {ticket_encontrado}")
        logger.info("")
        logger.info("🎫" * 40)
        logger.info("🎫" * 40)
        logger.info("")
        
        # Guardar ticket SIEMPRE
        ti.xcom_push(key='ticket', value=ticket_encontrado)
        ti.xcom_push(key='config', value=config)
    
    # Ahora verificar si hay errores SOAP Fault
    if 'soap:Fault' in response.text or 'faultstring' in response.text:
        log_titulo("⚠️ SE DETECTÓ SOAP FAULT EN LA RESPUESTA", "❌")
        
        fault_info = SICOPClient.parse_soap_fault(response.text)
        
        if fault_info:
            logger.info("")
            log_dato("Código SOAP Fault", fault_info['code'])
            logger.info("")
            logger.info("Mensaje del error:")
            logger.info("-" * 80)
            
            # Mostrar mensaje completo con formato
            mensaje = fault_info['message']
            for linea in mensaje.split('\n')[:50]:  # Primeras 50 líneas
                if linea.strip():
                    logger.info(f"  {linea.strip()}")
            
            logger.info("-" * 80)
            logger.info("")
            
            if fault_info['is_validation_error']:
                # Extraer errores por fila
                error_lines = [line.strip() for line in mensaje.split('\n') 
                              if line.strip() and 'Fila' in line and 'Error' in line]
                
                log_subtitulo(f"ERRORES DE VALIDACIÓN ENCONTRADOS: {len(error_lines)}")
                logger.info("")
                
                for i, error in enumerate(error_lines[:20], 1):
                    logger.info(f"  {i}. {error}")
                
                if len(error_lines) > 20:
                    logger.info(f"  ... y {len(error_lines) - 20} errores más")
                
                logger.info("")
                logger.info("💡 ACCIÓN REQUERIDA:")
                logger.info("  1. Revisa los errores listados arriba")
                logger.info("  2. Corrige el archivo CSV")
                logger.info("  3. Regenera el archivo ZIP")
                logger.info("  4. Vuelve a ejecutar el DAG")
                logger.info("")
                
                ti.xcom_push(key='validation_errors', value=error_lines)
                
                if ticket_encontrado:
                    logger.warning(f"⚠️ NOTA: Se obtuvo ticket {ticket_encontrado} pero hubo errores de validación")
                    logger.warning("   El ticket puede no ser útil debido a los errores")
                
                raise AirflowException(f"Validación CSV fallida: {len(error_lines)} errores")
            else:
                logger.error("")
                logger.error("❌ Error SOAP no relacionado con validación")
                logger.error("")
                raise AirflowException("Error SOAP en carga")
        else:
            logger.error("")
            logger.error("❌ No se pudo parsear el SOAP Fault")
            logger.error("   Ver XML completo arriba")
            logger.error("")
            raise AirflowException("SOAP Fault no parseado")
    
    # Si llegamos aquí y hay ticket, es exitoso
    if ticket_encontrado:
        log_titulo("✅ CARGA EXITOSA", "🎉")
        log_dato("Ticket", ticket_encontrado)
        log_dato("Instancia", config['instancia'])
        log_dato("Timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        logger.info("")
        
        return ticket_encontrado
    else:
        logger.error("")
        logger.error("❌ ERROR: No se encontró ticket en la respuesta")
        logger.error("   Ver XML completo arriba para investigar")
        logger.error("")
        raise AirflowException("Ticket no encontrado en respuesta exitosa")

def consultar_estado_ticket(**context):
    """Consulta el estado del ticket periódicamente"""
    ti = context['ti']
    ticket = ti.xcom_pull(task_ids='cargar_archivo_sicop')
    config = ti.xcom_pull(task_ids='cargar_archivo_sicop', key='config')
    
    if not ticket:
        logger.error("")
        logger.error("❌ ERROR: No se pudo recuperar el ticket")
        logger.error("   Verifica la tarea anterior")
        logger.error("")
        raise AirflowException("Ticket no disponible")
    
    log_titulo(f"MONITOREO DE TICKET: {ticket}", "🔍")
    
    try:
        ticket_long = int(ticket)
    except:
        ticket_long = ticket
    
    soap_payload = f"""<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ser="http://service.cargaoperacion.sicop.shcp.gob.mx/">
  <soapenv:Header/>
  <soapenv:Body>
    <ser:statusTicket>
      <in0>{config['instancia']}</in0>
      <in1>{ticket_long}</in1>
    </ser:statusTicket>
  </soapenv:Body>
</soapenv:Envelope>"""
    
    headers = {
        'Content-Type': 'text/xml; charset=utf-8',
        'SOAPAction': 'statusTicket',
        'User-Agent': 'Airflow-SICOP/2.10.2'
    }
    headers.update(SICOPClient.get_auth_header(config['usuario'], config['password']))
    
    url = SICOPClient.get_endpoint_url(config['ambiente'], config['ramo'])
    
    intentos = 0
    tiempo_total = 0
    
    # Estados finales que detienen el loop
    estados_finales = ["TERMINADO", "TERMINADO CON ERRORES", "RECHAZADO"]
    
    while intentos < config['max_intentos']:
        intentos += 1
        
        logger.info("")
        logger.info(f"📊 Consulta {intentos}/{config['max_intentos']} | Ticket: {ticket} | ⏱️ {tiempo_total/60:.1f} min")
        
        try:
            response = requests.post(
                url,
                params={'instancia': config['instancia']},
                data=soap_payload,
                headers=headers,
                timeout=60,
                verify=False
            )
            
            response.raise_for_status()
            
            # Mostrar XML cada 5 consultas o en la primera
            if intentos == 1 or intentos % 5 == 0:
                log_xml_formateado(f"RESPONSE statusTicket (consulta {intentos})", response.text)
            
            ti.xcom_push(key=f'response_xml_status_{intentos}', value=response.text)
            
            status_info = SICOPClient.parse_status_response(response.text)
            
            if status_info and status_info['estado']:
                estado = status_info['estado']
                errores = status_info['errores']
                
                log_dato("Estado", estado)
                
                # CASO 1: TERMINADO (éxito total)
                if estado == "TERMINADO":
                    logger.info("")
                    logger.info("✅" * 40)
                    logger.info("✅" * 40)
                    logger.info("")
                    logger.info(f"        PROCESO COMPLETADO - TICKET: {ticket}")
                    logger.info("")
                    logger.info("✅" * 40)
                    logger.info("✅" * 40)
                    logger.info("")
                    
                    log_dato("Tiempo total", f"{tiempo_total/60:.1f} minutos")
                    log_dato("Consultas realizadas", intentos)
                    logger.info("")
                    
                    if errores:
                        logger.info("ℹ️ Mensajes adicionales:")
                        for i, error in enumerate(errores[:10], 1):
                            logger.info(f"  {i}. {error}")
                        ti.xcom_push(key='mensajes_adicionales', value=errores)
                    
                    ti.xcom_push(key='estado_final', value=estado)
                    ti.xcom_push(key='ticket_final', value=ticket)
                    ti.xcom_push(key='tiempo_procesamiento', value=tiempo_total)
                    
                    return estado
                
                # CASO 2: TERMINADO CON ERRORES (completado pero con advertencias)
                elif estado == "TERMINADO CON ERRORES":
                    logger.warning("")
                    logger.warning("⚠️" * 40)
                    logger.warning("⚠️" * 40)
                    logger.warning("")
                    logger.warning(f"    PROCESO COMPLETADO CON ERRORES - TICKET: {ticket}")
                    logger.warning("")
                    logger.warning("⚠️" * 40)
                    logger.warning("⚠️" * 40)
                    logger.warning("")
                    
                    log_dato("Tiempo total", f"{tiempo_total/60:.1f} minutos")
                    log_dato("Consultas realizadas", intentos)
                    logger.warning("")
                    
                    if errores:
                        logger.warning(f"⚠️ Se encontraron {len(errores)} mensaje(s) de error:")
                        logger.warning("")
                        for i, error in enumerate(errores[:20], 1):
                            logger.warning(f"  {i}. {error}")
                        
                        if len(errores) > 20:
                            logger.warning(f"  ... y {len(errores) - 20} errores más")
                        
                        logger.warning("")
                        ti.xcom_push(key='errores_procesamiento', value=errores)
                    
                    ti.xcom_push(key='estado_final', value=estado)
                    ti.xcom_push(key='ticket_final', value=ticket)
                    ti.xcom_push(key='tiempo_procesamiento', value=tiempo_total)
                    
                    return estado
                
                # CASO 3: RECHAZADO (error total)
                elif estado == "RECHAZADO":
                    log_xml_formateado("⚠️ RESPONSE COMPLETO - PROCESO RECHAZADO", response.text)
                    
                    logger.error("")
                    logger.error("❌" * 40)
                    logger.error("❌" * 40)
                    logger.error("")
                    logger.error(f"        PROCESO RECHAZADO - TICKET: {ticket}")
                    logger.error("")
                    logger.error("❌" * 40)
                    logger.error("❌" * 40)
                    logger.error("")
                    
                    log_dato("Tiempo hasta rechazo", f"{tiempo_total/60:.1f} minutos")
                    log_dato("Consultas realizadas", intentos)
                    logger.error("")
                    
                    if errores:
                        logger.error(f"❌ Se encontraron {len(errores)} error(es):")
                        logger.error("")
                        
                        for i, error in enumerate(errores[:20], 1):
                            logger.error(f"  {i}. {error}")
                        
                        if len(errores) > 20:
                            logger.error(f"  ... y {len(errores) - 20} errores más")
                        
                        logger.error("")
                        ti.xcom_push(key='errores_procesamiento', value=errores)
                    
                    ti.xcom_push(key='estado_final', value=estado)
                    ti.xcom_push(key='ticket_final', value=ticket)
                    ti.xcom_push(key='tiempo_procesamiento', value=tiempo_total)
                    
                    return estado
                
                # CASO 4: EN PROCESO (seguir esperando)
                elif estado == "EN PROCESO":
                    logger.info(f"  ⏳ Procesando... próxima consulta en {config['intervalo']}s")
                    time.sleep(config['intervalo'])
                    tiempo_total += config['intervalo']
                    continue
                
                # CASO 5: Estado desconocido pero verificar si es final
                else:
                    logger.warning(f"  ❓ Estado no reconocido: '{estado}'")
                    
                    # Verificar si contiene alguna palabra clave de finalización
                    estado_upper = estado.upper()
                    if "TERMINADO" in estado_upper or "COMPLETADO" in estado_upper or "FINALIZADO" in estado_upper:
                        logger.warning(f"  ℹ️ Interpretando '{estado}' como estado FINAL")
                        logger.warning(f"  ⚠️ Deteniendo monitoreo y continuando con procesar_resultado")
                        
                        if errores:
                            ti.xcom_push(key='errores_procesamiento', value=errores)
                        
                        ti.xcom_push(key='estado_final', value=estado)
                        ti.xcom_push(key='ticket_final', value=ticket)
                        ti.xcom_push(key='tiempo_procesamiento', value=tiempo_total)
                        
                        return estado
                    
                    # Si no parece final, seguir esperando
                    if intentos % 5 == 0:
                        log_xml_formateado(f"RESPONSE con estado '{estado}'", response.text)
                    
                    logger.warning(f"  ⏳ Esperando {config['intervalo']}s antes de reintentar...")
                    time.sleep(config['intervalo'])
                    tiempo_total += config['intervalo']
                    
            else:
                logger.warning("  ⚠️ No se pudo parsear el estado de la respuesta")
                if intentos <= 3:
                    log_xml_formateado("RESPONSE sin estado reconocible", response.text)
                time.sleep(config['intervalo'])
                tiempo_total += config['intervalo']
                
        except requests.exceptions.RequestException as e:
            logger.warning(f"  ⚠️ Error HTTP: {type(e).__name__} - {str(e)}")
            logger.warning(f"  ⏳ Reintentando en {config['intervalo']}s...")
            time.sleep(config['intervalo'])
            tiempo_total += config['intervalo']
        except Exception as e:
            logger.warning(f"  ⚠️ Error inesperado: {type(e).__name__} - {str(e)}")
            logger.warning(f"  ⏳ Reintentando en {config['intervalo']}s...")
            time.sleep(config['intervalo'])
            tiempo_total += config['intervalo']
    
    # Si llegamos aquí, se agotaron los intentos SIN obtener un estado final
    logger.error("")
    logger.error("⏱️" * 40)
    logger.error("⏱️ TIMEOUT EN MONITOREO DE TICKET")
    logger.error("⏱️" * 40)
    logger.error("")
    log_dato("Ticket", ticket)
    log_dato("Tiempo total", f"{tiempo_total/60:.0f} minutos")
    log_dato("Intentos realizados", config['max_intentos'])
    logger.error("")
    logger.error("💡 El proceso puede seguir ejecutándose en SICOP")
    logger.error("   Verifica manualmente el estado del ticket en el sistema")
    logger.error("")
    
    raise AirflowException(f"Timeout: {tiempo_total/60:.0f} min sin estado final - Ticket: {ticket}")

def procesar_resultado(**context):
    """Procesa el resultado final"""
    ti = context['ti']
    estado = ti.xcom_pull(task_ids='consultar_estado_ticket', key='estado_final')
    ticket = ti.xcom_pull(task_ids='consultar_estado_ticket', key='ticket_final')
    errores = ti.xcom_pull(task_ids='consultar_estado_ticket', key='errores_procesamiento')
    tiempo = ti.xcom_pull(task_ids='consultar_estado_ticket', key='tiempo_procesamiento')
    
    log_titulo(f"RESUMEN FINAL - TICKET: {ticket}", "📋")
    
    logger.info("")
    log_dato("🎫 Ticket", ticket)
    log_dato("📊 Estado", estado)
    log_dato("🌍 Ambiente", Variable.get('SICOP_AMBIENTE', 'calidad').upper())
    log_dato("🏢 Instancia", Variable.get('SICOP_INSTANCIA', 'SICOP25'))
    log_dato("⏱️ Tiempo de procesamiento", f"{tiempo/60:.1f} minutos" if tiempo else "N/A")
    log_dato("⚠️ Errores/Mensajes", len(errores) if errores else 0)
    log_dato("🕐 Timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    logger.info("")
    
    # Clasificar el resultado
    if estado == "TERMINADO":
        logger.info("🎉 RESULTADO: ÉXITO TOTAL")
        logger.info("   El archivo fue procesado exitosamente sin errores")
        resultado_tipo = "EXITO"
        
    elif estado == "TERMINADO CON ERRORES":
        logger.warning("⚠️ RESULTADO: COMPLETADO CON ADVERTENCIAS")
        logger.warning("   El proceso finalizó pero se encontraron advertencias")
        if errores:
            logger.warning(f"   Total de advertencias: {len(errores)}")
        resultado_tipo = "EXITO_CON_ADVERTENCIAS"
        
    elif estado == "RECHAZADO":
        logger.error("❌ RESULTADO: RECHAZADO")
        logger.error("   El proceso fue rechazado por SICOP")
        if errores:
            logger.error(f"   Total de errores: {len(errores)}")
        resultado_tipo = "ERROR"
        
    else:
        logger.warning(f"❓ RESULTADO: ESTADO DESCONOCIDO '{estado}'")
        resultado_tipo = "DESCONOCIDO"
    
    logger.info("")
    
    resultado = {
        'ticket': ticket,
        'estado': estado,
        'resultado_tipo': resultado_tipo,
        'errores': errores or [],
        'tiempo_procesamiento_segundos': tiempo,
        'timestamp': datetime.now().isoformat(),
        'ambiente': Variable.get('SICOP_AMBIENTE', 'calidad'),
        'instancia': Variable.get('SICOP_INSTANCIA', 'SICOP25')
    }
    
    ti.xcom_push(key='resultado_completo', value=resultado)
    
    return resultado_tipo

# Definir el DAG
with DAG(
    dag_id='sicop_carga_operacion_robusto',
    default_args=default_args,
    description='Carga robusta de operaciones en SICOP con manejo completo de errores',
    schedule_interval='0 8 * * 1-6',  # Lunes a Sábado 8:00 AM
    start_date=datetime(2024, 1, 1),
    catchup=False,
    max_active_runs=1,
    dagrun_timeout=timedelta(hours=3),
    tags=['SICOP', 'SHCP', 'produccion'],
) as dag:
    
    t1_validar = PythonOperator(
        task_id='validar_configuracion',
        python_callable=validar_configuracion,
        provide_context=True,
    )
    
    t2_cargar = PythonOperator(
        task_id='cargar_archivo_sicop',
        python_callable=cargar_archivo_sicop,
        provide_context=True,
    )
    
    t3_consultar = PythonOperator(
        task_id='consultar_estado_ticket',
        python_callable=consultar_estado_ticket,
        provide_context=True,
    )
    
    t4_procesar = PythonOperator(
        task_id='procesar_resultado',
        python_callable=procesar_resultado,
        provide_context=True,
    )
    
    # Flujo del DAG
    t1_validar >> t2_cargar >> t3_consultar >> t4_procesar