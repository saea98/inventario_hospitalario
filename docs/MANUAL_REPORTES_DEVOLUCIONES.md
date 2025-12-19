# Manual de Reportes y Análisis Avanzados de Devoluciones
## Fase 2.5 - Sistema de Inventario Hospitalario

**Versión:** 1.0  
**Fecha:** Diciembre 2025  
**Autor:** Sistema de Inventario Hospitalario

---

## 📋 Tabla de Contenidos

1. [Introducción](#introducción)
2. [Acceso a Reportes](#acceso-a-reportes)
3. [Reporte General](#reporte-general)
4. [Análisis de Proveedores](#análisis-de-proveedores)
5. [Análisis Temporal](#análisis-temporal)
6. [Interpretación de Gráficos](#interpretación-de-gráficos)
7. [Filtros y Búsquedas](#filtros-y-búsquedas)
8. [Casos de Uso](#casos-de-uso)
9. [Preguntas Frecuentes](#preguntas-frecuentes)
10. [Documentación Técnica](#documentación-técnica)

---

## Introducción

La Fase 2.5 introduce un conjunto completo de reportes y análisis avanzados para el módulo de Devoluciones de Proveedores. Estos reportes permiten:

- **Visualizar tendencias** de devoluciones en el tiempo
- **Analizar proveedores** con mayor cantidad de devoluciones
- **Identificar patrones** en los motivos de devolución
- **Tomar decisiones** basadas en datos concretos
- **Monitorear desempeño** de la gestión de devoluciones

### Objetivos Principales

✅ Proporcionar visibilidad completa de las devoluciones  
✅ Identificar proveedores problemáticos  
✅ Analizar tendencias temporales  
✅ Facilitar la toma de decisiones  
✅ Mejorar la gestión de proveedores  

---

## Acceso a Reportes

### Ubicación en el Menú

```
Gestión Logística
├── Citas de Proveedores
├── Traslados
├── Conteo Físico
├── Gestión de Pedidos
├── Propuestas de Surtimiento
├── Llegada de Proveedores
├── Devoluciones de Proveedores
└── Reportes de Devoluciones ✨ NUEVO
    ├── Reporte General
    ├── Análisis de Proveedores
    └── Análisis Temporal
```

### URLs Directas

| Reporte | URL |
|---------|-----|
| Reporte General | `/reportes/devoluciones/reporte-general/` |
| Análisis de Proveedores | `/reportes/devoluciones/analisis-proveedores/` |
| Análisis Temporal | `/reportes/devoluciones/analisis-temporal/` |

---

## Reporte General

### Descripción

El Reporte General proporciona una visión general de todas las devoluciones con estadísticas clave y gráficos interactivos.

### Estadísticas Mostradas

| Métrica | Descripción |
|---------|-------------|
| **Total Devoluciones** | Número total de devoluciones registradas |
| **Monto Total** | Suma total de valores devueltos |
| **Total Items** | Cantidad total de items devueltos |
| **Promedio por Devolución** | Monto promedio por devolución |

### Gráficos Disponibles

#### 1. Devoluciones por Estado (Gráfico de Doughnut)

**Qué muestra:**
- Distribución de devoluciones por estado (Pendiente, Autorizada, Completada, Cancelada)
- Porcentaje de cada estado

**Cómo interpretarlo:**
- Un alto porcentaje en "Pendiente" indica devoluciones sin procesar
- Un alto porcentaje en "Completada" indica buen flujo de devoluciones
- Un alto porcentaje en "Cancelada" puede indicar problemas

#### 2. Devoluciones por Proveedor (Gráfico de Barras)

**Qué muestra:**
- Top 10 proveedores con más devoluciones
- Cantidad de devoluciones por proveedor

**Cómo interpretarlo:**
- Proveedores con más devoluciones requieren seguimiento
- Pueden indicar problemas de calidad o cumplimiento

### Tabla de Resumen por Estado

Muestra:
- Cantidad de devoluciones por estado
- Monto total por estado
- Porcentaje de cada estado

### Filtros Disponibles

| Filtro | Descripción |
|--------|-------------|
| **Fecha Inicio** | Filtra devoluciones desde esta fecha |
| **Fecha Fin** | Filtra devoluciones hasta esta fecha |
| **Estado** | Filtra por estado específico |
| **Proveedor** | Filtra por proveedor específico |

### Paso a Paso

1. Accede a "Gestión Logística" → "Reportes de Devoluciones" → "Reporte General"
2. (Opcional) Establece los filtros deseados
3. Haz clic en "Filtrar"
4. Visualiza las estadísticas y gráficos
5. Desplázate hacia abajo para ver la tabla de últimas devoluciones

---

## Análisis de Proveedores

### Descripción

Proporciona análisis detallado de cada proveedor, incluyendo cantidad de devoluciones, montos, motivos y estados.

### Información por Proveedor

| Campo | Descripción |
|-------|-------------|
| **Proveedor** | Nombre del proveedor |
| **Total Devoluciones** | Cantidad de devoluciones del proveedor |
| **Monto Total** | Suma total devuelto al proveedor |
| **Items Devueltos** | Cantidad total de items |
| **Promedio por Devolución** | Monto promedio |
| **Pendientes** | Devoluciones en estado Pendiente |
| **Autorizadas** | Devoluciones en estado Autorizada |
| **Completadas** | Devoluciones en estado Completada |
| **Canceladas** | Devoluciones en estado Cancelada |

### Gráficos Disponibles

#### 1. Motivos Más Frecuentes (Gráfico de Barras)

**Qué muestra:**
- Los 10 motivos de devolución más comunes
- Cantidad de devoluciones por motivo

**Cómo interpretarlo:**
- Motivos frecuentes pueden indicar problemas sistémicos
- Permite enfocarse en las causas raíz

#### 2. Monto Total por Proveedor (Gráfico de Barras)

**Qué muestra:**
- Top 5 proveedores por monto total devuelto
- Impacto financiero de cada proveedor

**Cómo interpretarlo:**
- Proveedores con montos altos requieren atención prioritaria
- Pueden afectar significativamente el presupuesto

### Tabla de Motivos Frecuentes

Muestra:
- Motivo de devolución
- Cantidad de veces que ocurrió
- Monto total asociado
- Barra de progreso con porcentaje

### Filtros Disponibles

| Filtro | Descripción |
|--------|-------------|
| **Fecha Inicio** | Filtra devoluciones desde esta fecha |
| **Fecha Fin** | Filtra devoluciones hasta esta fecha |

### Paso a Paso

1. Accede a "Gestión Logística" → "Reportes de Devoluciones" → "Análisis de Proveedores"
2. (Opcional) Establece el rango de fechas
3. Haz clic en "Filtrar"
4. Visualiza los gráficos de motivos y proveedores
5. Desplázate para ver el análisis detallado por proveedor
6. Revisa los motivos más frecuentes en la tabla inferior

---

## Análisis Temporal

### Descripción

Analiza las tendencias de devoluciones a lo largo del tiempo, permitiendo identificar patrones estacionales y cambios en el comportamiento.

### Estadísticas Temporales

| Métrica | Descripción |
|---------|-------------|
| **Tiempo Promedio de Autorización** | Días promedio para autorizar una devolución |
| **Tiempo Promedio de Entrega** | Días promedio para completar una devolución |

### Gráfico de Tendencia

**Tipo:** Gráfico de líneas dual

**Qué muestra:**
- Línea azul: Cantidad de devoluciones por período
- Línea verde: Monto total devuelto por período
- Eje Y izquierdo: Cantidad (escala de devoluciones)
- Eje Y derecho: Monto en $ (escala de dinero)

**Cómo interpretarlo:**
- Picos en cantidad pueden indicar períodos problemáticos
- Tendencia creciente indica aumento de devoluciones
- Correlación entre cantidad y monto muestra consistencia

### Tabla de Datos por Período

Muestra:
- Período (mes/año)
- Cantidad de devoluciones
- Monto total
- Cantidad de items
- Promedio por devolución

### Filtros Disponibles

| Filtro | Descripción |
|--------|-------------|
| **Período** | Por Mes o Por Año |

### Paso a Paso

1. Accede a "Gestión Logística" → "Reportes de Devoluciones" → "Análisis Temporal"
2. Selecciona el tipo de período (Mes o Año)
3. Haz clic en "Filtrar"
4. Visualiza el gráfico de tendencia
5. Revisa las estadísticas de tiempo promedio
6. Desplázate para ver la tabla de datos detallados

---

## Interpretación de Gráficos

### Gráfico de Doughnut (Pastel)

**Cuándo usarlo:**
- Para mostrar proporciones de un total
- Para comparar partes de un todo

**Cómo leerlo:**
- Cada segmento representa una categoría
- El tamaño del segmento es proporcional al valor
- Los colores ayudan a diferenciar categorías

### Gráfico de Barras

**Cuándo usarlo:**
- Para comparar valores entre categorías
- Para mostrar rankings

**Cómo leerlo:**
- La altura de la barra representa el valor
- Barras más altas = valores más grandes
- Útil para identificar máximos y mínimos

### Gráfico de Líneas

**Cuándo usarlo:**
- Para mostrar tendencias en el tiempo
- Para identificar patrones

**Cómo leerlo:**
- La posición vertical representa el valor
- La pendiente muestra velocidad de cambio
- Picos y valles indican variaciones

---

## Filtros y Búsquedas

### Filtro por Fecha

**Rango de Fechas:**
- Selecciona "Fecha Inicio" y "Fecha Fin"
- El sistema filtra devoluciones dentro del rango
- Formato: YYYY-MM-DD

**Ejemplo:**
- Inicio: 2025-01-01
- Fin: 2025-12-31
- Resultado: Todas las devoluciones de 2025

### Filtro por Estado

**Estados Disponibles:**
- **PENDIENTE:** Devolución registrada, sin autorizar
- **AUTORIZADA:** Devolución autorizada, pendiente de entrega
- **COMPLETADA:** Devolución completada y entregada
- **CANCELADA:** Devolución cancelada

### Filtro por Proveedor

**Cómo usar:**
1. Haz clic en el dropdown de "Proveedor"
2. Selecciona el proveedor deseado
3. Haz clic en "Filtrar"

**Resultado:**
- Solo se muestran devoluciones del proveedor seleccionado

### Filtro por Período

**Opciones:**
- **Por Mes:** Agrupa datos por mes (últimos 12 meses)
- **Por Año:** Agrupa datos por año

---

## Casos de Uso

### Caso 1: Identificar Proveedores Problemáticos

**Objetivo:** Encontrar proveedores con alta tasa de devoluciones

**Pasos:**
1. Accede a "Análisis de Proveedores"
2. Revisa la tabla de análisis detallado
3. Ordena por "Total Devoluciones" (descendente)
4. Identifica los proveedores con más devoluciones
5. Toma acciones correctivas (renegociar términos, cambiar proveedor, etc.)

### Caso 2: Analizar Motivos de Devolución

**Objetivo:** Entender por qué se devuelven productos

**Pasos:**
1. Accede a "Análisis de Proveedores"
2. Revisa la tabla "Motivos de Devolución Más Frecuentes"
3. Identifica los motivos más comunes
4. Comunica con proveedores sobre estos motivos
5. Implementa mejoras

### Caso 3: Monitorear Tendencias

**Objetivo:** Identificar si las devoluciones están aumentando o disminuyendo

**Pasos:**
1. Accede a "Análisis Temporal"
2. Visualiza el gráfico de tendencia
3. Observa la pendiente de las líneas
4. Si está aumentando: Investiga causas
5. Si está disminuyendo: Celebra mejoras

### Caso 4: Evaluar Desempeño Operativo

**Objetivo:** Medir qué tan rápido se procesan las devoluciones

**Pasos:**
1. Accede a "Análisis Temporal"
2. Revisa "Tiempo Promedio de Autorización"
3. Revisa "Tiempo Promedio de Entrega"
4. Compara con estándares internos
5. Identifica cuellos de botella

### Caso 5: Reporte Ejecutivo

**Objetivo:** Presentar un resumen a la gerencia

**Pasos:**
1. Accede a "Reporte General"
2. Captura las estadísticas principales
3. Captura los gráficos
4. Crea un documento con los hallazgos
5. Presenta recomendaciones

---

## Preguntas Frecuentes

### P1: ¿Cuál es la diferencia entre "Reporte General" y "Análisis de Proveedores"?

**R:** El Reporte General muestra un panorama completo de todas las devoluciones. El Análisis de Proveedores se enfoca específicamente en el desempeño de cada proveedor.

### P2: ¿Puedo exportar los reportes?

**R:** Actualmente, puedes capturar pantallas o usar las herramientas del navegador (Imprimir → PDF). En futuras versiones se agregará exportación directa a Excel y PDF.

### P3: ¿Con qué frecuencia se actualizan los datos?

**R:** Los datos se actualizan en tiempo real. Cada vez que registras una devolución o cambias su estado, los reportes se actualizan automáticamente.

### P4: ¿Puedo ver reportes históricos de años anteriores?

**R:** Sí, usa los filtros de fecha para seleccionar cualquier rango de fechas. Puedes ver datos desde el inicio del sistema.

### P5: ¿Qué significa "Tiempo Promedio de Autorización"?

**R:** Es el número de días promedio que tarda desde que se registra una devolución hasta que se autoriza. Un número bajo es mejor.

### P6: ¿Qué significa "Tiempo Promedio de Entrega"?

**R:** Es el número de días promedio que tarda desde que se registra una devolución hasta que se completa. Un número bajo es mejor.

### P7: ¿Por qué mi proveedor tiene muchas devoluciones?

**R:** Revisa los motivos de devolución. Pueden ser: defectos de calidad, empaque inadecuado, productos incorrectos, etc. Comunica con el proveedor.

### P8: ¿Cómo interpreto un gráfico con muchas fluctuaciones?

**R:** Las fluctuaciones pueden indicar variabilidad en el proceso. Busca patrones (ej: picos en ciertos meses) e investiga las causas.

### P9: ¿Qué hago si veo un aumento significativo en devoluciones?

**R:** Investiga las causas (cambio de proveedor, cambio de producto, cambio de proceso). Comunica con los equipos relevantes.

### P10: ¿Puedo compartir los reportes con otros usuarios?

**R:** Sí, cualquier usuario con acceso al sistema puede acceder a los mismos reportes. Los datos se filtran por institución.

### P11: ¿Qué es un "motivo de devolución"?

**R:** Es la razón por la cual se devuelve un producto (ej: Defectuoso, Vencido, Cantidad Incorrecta, Producto Incorrecto, etc.).

### P12: ¿Cómo puedo mejorar mi tasa de devoluciones?

**R:** Identifica los motivos más frecuentes, comunica con proveedores, implementa controles de calidad, y monitorea el progreso con los reportes.

---

## Documentación Técnica

### Arquitectura

```
Vistas (views_reportes_devoluciones.py)
├── reporte_general_devoluciones()
├── analisis_proveedores()
├── analisis_temporal()
└── APIs JSON
    ├── api_grafico_estado()
    ├── api_grafico_proveedores()
    ├── api_grafico_tendencia()
    └── api_grafico_motivos()

Templates
├── reporte_general_devoluciones.html
├── analisis_proveedores.html
└── analisis_temporal.html

URLs (urls_reportes_devoluciones.py)
└── Rutas de acceso a vistas y APIs
```

### Modelos Utilizados

- **DevolucionProveedor:** Información de devoluciones
- **ItemDevolucion:** Items dentro de cada devolución
- **Proveedor:** Información del proveedor

### Agregaciones Utilizadas

| Agregación | Descripción |
|------------|-------------|
| `Count()` | Cuenta registros |
| `Sum()` | Suma valores |
| `Avg()` | Calcula promedio |
| `TruncMonth()` | Agrupa por mes |
| `TruncYear()` | Agrupa por año |

### APIs Disponibles

#### 1. API de Gráfico de Estados

**URL:** `/reportes/devoluciones/api/grafico-estado/`  
**Método:** GET  
**Respuesta:**
```json
{
    "labels": ["PENDIENTE", "AUTORIZADA", "COMPLETADA", "CANCELADA"],
    "data": [5, 10, 8, 2],
    "colors": ["#FFC107", "#17A2B8", "#28A745", "#6C757D"]
}
```

#### 2. API de Gráfico de Proveedores

**URL:** `/reportes/devoluciones/api/grafico-proveedores/`  
**Método:** GET  
**Respuesta:**
```json
{
    "labels": ["Proveedor A", "Proveedor B", "Proveedor C"],
    "data": [15, 12, 8]
}
```

#### 3. API de Gráfico de Tendencia

**URL:** `/reportes/devoluciones/api/grafico-tendencia/`  
**Método:** GET  
**Respuesta:**
```json
{
    "labels": ["Jan 2025", "Feb 2025", "Mar 2025"],
    "data_cantidad": [5, 8, 6],
    "data_monto": [1500.00, 2400.00, 1800.00]
}
```

#### 4. API de Gráfico de Motivos

**URL:** `/reportes/devoluciones/api/grafico-motivos/`  
**Método:** GET  
**Respuesta:**
```json
{
    "labels": ["DEFECTUOSO", "VENCIDO", "CANTIDAD_INCORRECTA"],
    "data": [12, 5, 3]
}
```

### Tecnologías Utilizadas

- **Backend:** Django 4.2
- **Base de Datos:** PostgreSQL
- **Frontend:** Bootstrap 5, Chart.js
- **JavaScript:** Vanilla JS para gráficos

### Permisos Requeridos

- Usuario debe estar autenticado (`@login_required`)
- Usuario debe tener institución asignada
- Los datos se filtran por institución del usuario

---

## Conclusión

Los reportes y análisis de la Fase 2.5 proporcionan herramientas poderosas para:

✅ Monitorear el desempeño de devoluciones  
✅ Identificar proveedores problemáticos  
✅ Analizar tendencias temporales  
✅ Tomar decisiones basadas en datos  
✅ Mejorar continuamente la gestión de devoluciones  

Utiliza estos reportes regularmente para mantener un control efectivo sobre las devoluciones de proveedores.

---

**Documento generado:** Diciembre 2025  
**Versión:** 1.0  
**Estado:** Completo
