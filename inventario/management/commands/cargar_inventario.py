# inventario/management/commands/cargar_inventario.py
from django.core.management.base import BaseCommand
import pandas as pd
from inventario.models import Producto, Lote, Institucion, OrdenSuministro, Proveedor, FuenteFinanciamiento
from decimal import Decimal
from datetime import datetime

class Command(BaseCommand):
    help = "Carga inventario desde inventario_hospital.xlsx"

    def add_arguments(self, parser):
        parser.add_argument("ruta_excel", type=str, help="Ruta al archivo inventario_hospital.xlsx")

    def handle(self, *args, **options):
        df = pd.read_excel(options["ruta_excel"])
        
        for _, row in df.iterrows():
            inst = Institucion.objects.filter(clue=row["CLUES"]).first()
            if not inst:
                continue  # saltar si la CLUE no está registrada

            proveedor, _ = Proveedor.objects.get_or_create(nombre=row["PROVEEDOR"])
            fuente, _ = FuenteFinanciamiento.objects.get_or_create(nombre=row["FUENTE DE FINACIAMIENTO"])
            orden, _ = OrdenSuministro.objects.get_or_create(
                numero=row["ORDEN DE SUMINISTRO"], proveedor=proveedor, fuente=fuente
            )

            producto, _ = Producto.objects.get_or_create(
                clave_cnis=row["CLAVE/CNIS"],
                defaults={"descripcion": row["DESCRIPCIÓN"], "precio_referencia": Decimal(str(row["PRECIO UNITARIO"]))}
            )

            fecha_cad = None
            if not pd.isna(row["FECHA DE CADUCIDAD"]):
                fecha_cad = pd.to_datetime(row["FECHA DE CADUCIDAD"]).date()

            Lote.objects.update_or_create(
                producto=producto, institucion=inst, lote=row["LOTE"],
                defaults={
                    "cantidad": Decimal(str(row["INVENTARIO DISPONIBLE"])),
                    "precio_unitario": Decimal(str(row["PRECIO UNITARIO"])),
                    "fecha_caducidad": fecha_cad,
                    "orden_suministro": orden,
                }
            )
        self.stdout.write(self.style.SUCCESS("Inventario cargado correctamente"))
