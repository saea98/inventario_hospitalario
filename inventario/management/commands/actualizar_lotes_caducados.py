"""
Marca lotes vencidos como caducados (equivalente al DAG Airflow actualizar_lotes_caducados).

En el host con Docker (contenedor inventario_dev, WORKDIR /app), vía script:
  0 2 * * * /ruta/al/repo/scripts/cron_actualizar_lotes_caducados.sh

O una línea:
  0 2 * * * docker exec inventario_dev sh -c 'cd /app && python manage.py actualizar_lotes_caducados' >>/var/log/lotes_caducados.log 2>&1

Sin Docker (venv en el servidor):
  0 2 * * * cd /ruta/al/proyecto && /ruta/venv/bin/python manage.py actualizar_lotes_caducados >>/var/log/lotes_caducados.log 2>&1

Variables .env (opcional, para Telegram): TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID o TELEGRAM_CHAT_ID_ALERTAS
"""
import requests
from decouple import config
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from inventario.models import Lote

ESTADO_DISPONIBLE = 1
ESTADO_CADUCADO = 6


class Command(BaseCommand):
    help = (
        'Marca como caducados los lotes con fecha de caducidad ya vencida, '
        'estado Disponible y cantidad disponible > 0.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Listar lotes afectados sin aplicar cambios',
        )
        parser.add_argument(
            '--no-telegram',
            action='store_true',
            help='No enviar notificación por Telegram aunque esté configurada',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        no_telegram = options['no_telegram']
        hoy = timezone.localdate()

        qs = (
            Lote.objects.filter(
                fecha_caducidad__lt=hoy,
                cantidad_disponible__gt=0,
                estado=ESTADO_DISPONIBLE,
            )
            .select_related('producto')
            .order_by('fecha_caducidad')
        )

        lotes = list(qs)
        if not lotes:
            self.stdout.write(self.style.SUCCESS('No hay lotes caducados pendientes de marcar.'))
            return

        self.stdout.write(f'Encontrados {len(lotes)} lotes a marcar como caducados.')

        if dry_run:
            for l in lotes[:25]:
                self.stdout.write(
                    f'  [dry-run] {l.numero_lote} | {l.producto.clave_cnis} | cad={l.fecha_caducidad}'
                )
            if len(lotes) > 25:
                self.stdout.write(f'  ... y {len(lotes) - 25} más')
            self.stdout.write(self.style.WARNING('Modo dry-run: no se aplicaron cambios.'))
            return

        now = timezone.now()
        actualizados = []
        telegram_filas = []
        for l in lotes:
            fc = l.fecha_caducidad
            cant_antes = l.cantidad_disponible
            p = l.producto
            telegram_filas.append(
                {
                    'numero_lote': l.numero_lote,
                    'producto': p.descripcion,
                    'clave_cnis': p.clave_cnis,
                    'fecha_caducidad': fc,
                    'cantidad': cant_antes,
                }
            )
            l.estado = ESTADO_CADUCADO
            l.cantidad_disponible = 0
            l.motivo_cambio_estado = (
                f'Lote marcado como caducado automáticamente (cron). Fecha caducidad: {fc}'
            )
            l.fecha_cambio_estado = now
            l.fecha_actualizacion = now
            actualizados.append(l)

        with transaction.atomic():
            Lote.objects.bulk_update(
                actualizados,
                [
                    'estado',
                    'cantidad_disponible',
                    'motivo_cambio_estado',
                    'fecha_cambio_estado',
                    'fecha_actualizacion',
                ],
            )

        self.stdout.write(self.style.SUCCESS(f'Actualizados {len(actualizados)} lotes.'))

        if not no_telegram:
            self._enviar_telegram(telegram_filas)

    def _enviar_telegram(self, filas):
        token = config('TELEGRAM_BOT_TOKEN', default='').strip()
        chat = config('TELEGRAM_CHAT_ID', default='').strip() or config(
            'TELEGRAM_CHAT_ID_ALERTAS', default=''
        ).strip()
        if not token or not chat:
            self.stdout.write(
                self.style.WARNING(
                    'Telegram no configurado (TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID o '
                    'TELEGRAM_CHAT_ID_ALERTAS); se omite notificación.'
                )
            )
            return

        mensaje = '🚨 *Reporte de Lotes Caducados*\n\n'
        mensaje += f"📅 Fecha: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        mensaje += f'📦 Total de lotes caducados: {len(filas)}\n\n'
        mensaje += '*Lotes procesados:*\n'
        for row in filas[:10]:
            mensaje += f"• *{row['numero_lote']}* - {row['producto']}\n"
            mensaje += f"  Clave CNIS: {row['clave_cnis']} | Cantidad: {row['cantidad']}\n"
            mensaje += f"  Caducidad: {row['fecha_caducidad']}\n"
        if len(filas) > 10:
            mensaje += f'\n... y {len(filas) - 10} lotes más\n'
        mensaje += '\n✅ Los lotes han sido marcados como caducados y no disponibles'

        url = f'https://api.telegram.org/bot{token}/sendMessage'
        try:
            r = requests.post(
                url,
                json={'chat_id': chat, 'text': mensaje, 'parse_mode': 'Markdown'},
                timeout=15,
            )
            if r.status_code == 200:
                self.stdout.write(self.style.SUCCESS('Notificación Telegram enviada.'))
            else:
                self.stdout.write(
                    self.style.ERROR(f'Telegram respondió {r.status_code}: {r.text[:500]}')
                )
        except requests.RequestException as e:
            self.stdout.write(self.style.WARNING(f'No se pudo enviar Telegram: {e}'))
