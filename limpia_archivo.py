import pandas as pd

# === Cargar archivo Excel original ===
ruta_archivo = '/Users/Sjimenez/Library/Mobile Documents/com~apple~CloudDocs/clientes/marybel/almacen/fuentes/reporte_lluvia.xlsx'
df = pd.read_excel(ruta_archivo)

# === Eliminar columnas sin valor ===
columnas_a_eliminar = ['Unnamed: 0', 'Unnamed: 1']
df = df.drop(columns=[col for col in columnas_a_eliminar if col in df.columns])

# === Normalizar texto ===
columnas_texto = [
    'PROVEEDOR', 'RFC', 'DESCRIPCIÓN', 'DESCRIPCIÓN (SAICA)', 'CLAVE', 'CLAVE (SAICA)',
    'PARTIDA', 'MARCA', 'FABRICANTE', 'TIPO DE ENTREGA', 'LICITACION/PROCEDIMIENTO',
    'TIPO DE RED', 'FOLIO', 'OBSERVACIONES', 'FUENTE DE DATOS', 'EPA', 'CONTRATO',
    'REVISIÓN', 'PEDIDO'
]
for col in columnas_texto:
    if col in df.columns:
        df[col] = df[col].astype(str).str.upper().str.strip()

# === Asegurar que cantidades y precios sean numéricos ===
columnas_numericas = [
    'CANT', 'COSTO UNITARIO', 'PRECIO UNITARIO SIN IVA', 'PRECIO UNITARIO CON IVA',
    'SUBTOTAL', 'IVA', 'IMPORTE TOTAL'
]
for col in columnas_numericas:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

# === Reemplazar NaN en texto con cadena vacía ===
df = df.fillna('')

# === Guardar CSV limpio sin agrupar ===
df.to_csv('archivo_limpio_para_carga.csv', index=False, encoding='utf-8-sig')

print(f"✅ Archivo limpio generado: {len(df)} filas (sin agrupar)")
