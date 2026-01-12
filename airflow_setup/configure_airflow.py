#!/usr/bin/env python3
"""
Script para configurar variables y conexiones de Airflow de forma interactiva.

Uso:
    python3 configure_airflow.py
"""

import os
import sys
import subprocess
from pathlib import Path


def run_command(cmd):
    """Ejecuta un comando en el contenedor de Airflow."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)


def set_airflow_variable(key, value):
    """Establece una variable de Airflow."""
    cmd = f'docker exec airflow_webserver airflow variables set "{key}" "{value}"'
    success, stdout, stderr = run_command(cmd)
    return success


def create_connection(conn_id, conn_type, host, port, login, password, schema):
    """Crea una conexión en Airflow."""
    cmd = f'docker exec airflow_webserver airflow connections add "{conn_id}" ' \
          f'--conn-type "{conn_type}" ' \
          f'--conn-host "{host}" ' \
          f'--conn-port "{port}" ' \
          f'--conn-login "{login}" ' \
          f'--conn-password "{password}" ' \
          f'--conn-schema "{schema}"'
    success, stdout, stderr = run_command(cmd)
    return success


def main():
    print("=" * 60)
    print("🔧 Configurador de Airflow - Inventario Hospitalario")
    print("=" * 60)
    print()

    # Verificar que Airflow esté corriendo
    print("✓ Verificando que Airflow esté disponible...")
    success, _, _ = run_command("docker exec airflow_webserver airflow version")
    if not success:
        print("✗ Error: No se puede conectar a Airflow")
        print("  Asegúrate de que los contenedores estén corriendo:")
        print("  docker-compose up -d")
        sys.exit(1)
    print("✓ Airflow disponible\n")

    # Configurar variables de Base de Datos
    print("=" * 60)
    print("📦 CONFIGURACIÓN DE BASE DE DATOS")
    print("=" * 60)
    
    db_host = input("Host de PostgreSQL [host.docker.internal]: ").strip() or "host.docker.internal"
    db_port = input("Puerto de PostgreSQL [5432]: ").strip() or "5432"
    db_name = input("Nombre de BD [inventario_hospitalario]: ").strip() or "inventario_hospitalario"
    db_user = input("Usuario de PostgreSQL [postgres]: ").strip() or "postgres"
    db_password = input("Contraseña de PostgreSQL [postgres]: ").strip() or "postgres"
    
    print("\n⏳ Guardando configuración de BD...")
    set_airflow_variable("DB_HOST", db_host)
    set_airflow_variable("DB_PORT", db_port)
    set_airflow_variable("DB_NAME", db_name)
    set_airflow_variable("DB_USER", db_user)
    set_airflow_variable("DB_PASSWORD", db_password)
    print("✓ Configuración de BD guardada\n")

    # Configurar variables de Telegram
    print("=" * 60)
    print("📱 CONFIGURACIÓN DE TELEGRAM")
    print("=" * 60)
    print("\nPara obtener tus credenciales de Telegram:")
    print("1. Bot Token: Crea un bot en @BotFather y obtén el token")
    print("2. Chat ID: Envía un mensaje a tu bot y obtén el chat_id de:")
    print("   https://api.telegram.org/bot<TOKEN>/getUpdates\n")
    
    telegram_token = input("Token del Bot de Telegram: ").strip()
    telegram_chat_id = input("Chat ID de Telegram: ").strip()
    
    if telegram_token and telegram_chat_id:
        print("\n⏳ Guardando configuración de Telegram...")
        set_airflow_variable("TELEGRAM_BOT_TOKEN", telegram_token)
        set_airflow_variable("TELEGRAM_CHAT_ID", telegram_chat_id)
        set_airflow_variable("NOTIFICATION_ENABLED", "true")
        print("✓ Configuración de Telegram guardada")
    else:
        print("\n⚠️  Telegram no configurado (opcional)")
        set_airflow_variable("NOTIFICATION_ENABLED", "false")
    print()

    # Crear conexión a PostgreSQL
    print("=" * 60)
    print("🔗 CREAR CONEXIÓN A POSTGRESQL")
    print("=" * 60)
    
    print("\n⏳ Creando conexión 'postgres_inventario'...")
    success = create_connection(
        conn_id="postgres_inventario",
        conn_type="postgres",
        host=db_host,
        port=db_port,
        login=db_user,
        password=db_password,
        schema=db_name
    )
    
    if success:
        print("✓ Conexión 'postgres_inventario' creada\n")
    else:
        print("⚠️  La conexión podría ya existir\n")

    # Resumen final
    print("=" * 60)
    print("✅ CONFIGURACIÓN COMPLETADA")
    print("=" * 60)
    print()
    print("📊 Acceso a Airflow:")
    print("   URL: http://localhost:8080")
    print("   Usuario: admin")
    print("   Contraseña: admin")
    print()
    print("🌸 Acceso a Flower (Monitor de Celery):")
    print("   URL: http://localhost:5555")
    print()
    print("📝 Próximos pasos:")
    print("   1. Accede a http://localhost:8080")
    print("   2. Verifica que el DAG 'actualizar_lotes_caducados' esté visible")
    print("   3. Activa el DAG en la interfaz")
    print("   4. El DAG se ejecutará diariamente a las 2:00 AM")
    print()


if __name__ == "__main__":
    main()
