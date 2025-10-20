import pandas as pd

# Ruta del archivo (ajústala según tu entorno)
reporte_path = "/Users/Sjimenez/Library/Mobile Documents/com~apple~CloudDocs/clientes/marybel/almacen/fuentes/reporte_lluvia.xlsx"

# Leer todas las hojas del Excel
reporte = pd.read_excel(reporte_path, sheet_name=None)

# Seleccionar la hoja con más columnas (probablemente la principal)
reporte_df = max(reporte.values(), key=lambda x: x.shape[1])

# Normalizar los nombres de las columnas
reporte_df.columns = reporte_df.columns.str.strip()

# Mostrar un resumen de columnas detectadas
print("=== COLUMNAS DETECTADAS ===")
for i, col in enumerate(reporte_df.columns):
    print(f"{i+1}. {col}")

# Mostrar las primeras filas
print("\n=== PRIMERAS FILAS DEL ARCHIVO ===")
print(reporte_df.head(15).to_string())
