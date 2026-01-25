# Pasos para Reconstruir el Contenedor con WeasyPrint

## ⚠️ IMPORTANTE: Compatibilidad de Arquitectura

Si estás en una Mac M3 (ARM64) y producción es x86:
- El `docker-compose.yml` y `Dockerfile` están configurados para forzar la arquitectura `linux/amd64`
- Esto garantiza que las dependencias binarias (Pango, Cairo) sean compatibles con producción
- La emulación puede ser más lenta, pero asegura compatibilidad

## 1. Verificar dependencias

- WeasyPrint ya está en `requirements.txt`: `weasyprint==61.2`
- El Dockerfile ha sido actualizado para incluir las dependencias del sistema necesarias:
  - `libpango-1.0-0`
  - `libpangoft2-1.0-0`
  - `libpangocairo-1.0-0`
  - `libgdk-pixbuf2.0-0`
  - `libffi-dev`
  - `shared-mime-info`
- **Arquitectura forzada a `linux/amd64`** para compatibilidad con producción

## 2. Detener el contenedor actual (si está corriendo)

```bash
docker-compose down
```

## 3. Reconstruir la imagen sin usar caché (para asegurar que instale reportlab)

```bash
docker-compose build --no-cache web
```

O si prefieres reconstruir todo:

```bash
docker-compose build --no-cache
```

## 4. Iniciar el contenedor

```bash
docker-compose up -d
```

## 5. Verificar que reportlab se instaló correctamente

```bash
docker-compose exec web python -c "import reportlab; print('ReportLab version:', reportlab.Version)"
```

## 6. Ver los logs para confirmar que todo está bien

```bash
docker-compose logs web
```

## Alternativa: Reconstrucción rápida (sin detener)

Si el contenedor está corriendo y quieres reconstruirlo sin detenerlo:

```bash
# Reconstruir
docker-compose build --no-cache web

# Reiniciar el servicio
docker-compose up -d --force-recreate web
```

## Notas importantes:

- El flag `--no-cache` asegura que se instalen todas las dependencias desde cero, incluyendo reportlab
- Si tienes volúmenes montados (como en docker-compose.yml), los cambios en el código se reflejarán automáticamente
- La instalación de reportlab puede tardar unos minutos ya que compila algunas extensiones

## Verificar que funciona:

Una vez reconstruido, prueba generar un PDF EPA desde la interfaz:
- Ve a una llegada en estado `UBICACION` o `APROBADA`
- Haz clic en "Imprimir EPA"
- Debería generarse el PDF con headers y footers repetidos en todas las páginas
