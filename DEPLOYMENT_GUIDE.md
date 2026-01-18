# Guía de Despliegue - Sistema de Inventario Hospitalario

## Resumen de Cambios (Fase 2.2.2 - Llegada de Proveedores)

### Nuevos Campos Agregados

#### Modelo `LlegadaProveedor`
- **`almacen`** (ForeignKey): Campo editable para seleccionar el almacén de destino
- **`tipo_red`** (CharField): Selección entre "Red Fría" o "Red Seca"
- **`folio_validacion`** (CharField): Folio heredado de la validación anterior

#### Modelo `ItemLlegada`
- **`piezas_por_lote`** (IntegerField): Cantidad de piezas por lote (mínimo 1)

### Cambios en Formularios

#### `LlegadaProveedorForm`
- Agregados campos: `almacen`, `tipo_red`
- Ambos campos son editables por el usuario

#### `ItemLlegadaForm`
- Agregado campo: `piezas_por_lote`
- Widget con validación mínima de 1 pieza

### Cambios en Templates

#### `crear_llegada.html`
- Nuevas filas en formulario principal para `almacen` y `tipo_red`
- Nueva columna en tabla de items: "Piezas/Lote"
- JavaScript para validación en tiempo real:
  - Valida que `piezas_por_lote` sea igual a `cantidad_recibida`
  - Previene envío del formulario si la validación falla

### Funcionalidades Nuevas

1. **Validación de Piezas por Lote**
   - Suma de `piezas_por_lote` debe ser igual a `cantidad_recibida`
   - Validación en cliente (JavaScript) y servidor (Django)

2. **Cálculo Automático de IVA**
   - Claves que inician con 060, 080, 130, 379: IVA 16%
   - Otras claves: IVA 0%

3. **Almacén Editable**
   - Usuario puede seleccionar el almacén de destino en la llegada

## Pasos de Despliegue

### 1. Desarrollo (DEV)

```bash
# Clonar o actualizar repositorio
git clone https://github.com/saea98/inventario_hospitalario.git
cd inventario_hospitalario

# Crear y activar ambiente virtual
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate  # Windows

# Instalar dependencias
pip install -r requirements.txt

# Aplicar migraciones
python manage.py migrate

# Ejecutar validación
python manage.py shell < deployment_validation.py
# o
ENVIRONMENT=DEV python deployment_validation.py

# Ejecutar servidor de desarrollo
python manage.py runserver
```

### 2. Calidad (QA)

```bash
# Actualizar código
git pull origin main

# Aplicar migraciones en QA
docker-compose -f docker-compose.qa.yml exec web python manage.py migrate

# Ejecutar validación
docker-compose -f docker-compose.qa.yml exec web python deployment_validation.py

# Reiniciar servicios
docker-compose -f docker-compose.qa.yml restart web
```

### 3. Productivo (PROD)

```bash
# Backup de base de datos
docker-compose -f docker-compose.prod.yml exec db pg_dump -U postgres inventario > backup_$(date +%Y%m%d_%H%M%S).sql

# Actualizar código
git pull origin main

# Aplicar migraciones en PROD
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate

# Ejecutar validación
docker-compose -f docker-compose.prod.yml exec web python deployment_validation.py

# Reiniciar servicios
docker-compose -f docker-compose.prod.yml restart web
```

## Validación Post-Despliegue

### Checklist

- [ ] Script de validación ejecutado exitosamente
- [ ] Modelos cargados correctamente
- [ ] Formularios con nuevos campos visibles
- [ ] Base de datos accesible
- [ ] Templates renderizados correctamente
- [ ] Validación JavaScript funcionando
- [ ] Cálculos de IVA correctos

### Pruebas Manuales

1. **Crear Nueva Llegada**
   - Navegar a `/logistica/llegadas/crear/`
   - Seleccionar una cita autorizada
   - Llenar datos de almacén y tipo de red
   - Agregar items con piezas_por_lote
   - Verificar validación de suma de piezas

2. **Validar Cálculos**
   - Crear item con clave 060001 (debe tener IVA 16%)
   - Crear item con clave 010001 (debe tener IVA 0%)
   - Verificar cálculos en facturación

3. **Verificar Almacén Editable**
   - Confirmar que almacén se puede cambiar en la llegada
   - Guardar y verificar que se guarda correctamente

## Rollback (en caso de problemas)

### Revertir Cambios

```bash
# Revertir último commit
git revert HEAD

# Revertir migraciones
python manage.py migrate inventario 0021_update_criterios_na

# Restaurar backup (PROD)
docker-compose -f docker-compose.prod.yml exec db psql -U postgres inventario < backup_YYYYMMDD_HHMMSS.sql
```

## Monitoreo Post-Despliegue

### Logs a Revisar

```bash
# Logs de Django
docker-compose logs -f web

# Logs de Base de Datos
docker-compose logs -f db

# Errores específicos
docker-compose exec web python manage.py shell
>>> from inventario.llegada_models import LlegadaProveedor
>>> LlegadaProveedor.objects.all().count()
```

### Métricas Importantes

- Tiempo de carga de formulario de llegada
- Errores de validación JavaScript
- Errores de cálculo de IVA
- Tiempo de guardado de llegadas

## Soporte y Contacto

En caso de problemas durante el despliegue:

1. Revisar logs de error
2. Ejecutar script de validación
3. Contactar al equipo de desarrollo
4. Preparar rollback si es necesario

## Notas Importantes

- Las migraciones deben aplicarse en orden
- Hacer backup antes de despliegue en PROD
- Validar en QA antes de pasar a PROD
- Documentar cualquier cambio manual realizado
- Comunicar cambios al equipo de usuarios

## Cronograma Sugerido

| Ambiente | Fecha | Hora | Responsable |
|----------|-------|------|-------------|
| DEV | Hoy | 10:00 | Desarrollador |
| QA | Mañana | 14:00 | QA Lead |
| PROD | Próxima Semana | 02:00 | DevOps |

---

**Versión**: 1.0  
**Fecha**: 2025-01-17  
**Autor**: Sistema de Inventario Hospitalario
