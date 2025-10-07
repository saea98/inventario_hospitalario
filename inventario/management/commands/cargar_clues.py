# inventario/management/commands/cargar_clues.py
from django.core.management.base import BaseCommand
import pandas as pd
from inventario.models import Institucion, Alcaldia, TipoInstitucion

class Command(BaseCommand):
    help = "Carga instituciones desde CLUES.xlsx"

    def add_arguments(self, parser):
        parser.add_argument("ruta_excel", type=str, help="Ruta al archivo CLUES.xlsx")

    def handle(self, *args, **options):
        df = pd.read_excel(options["ruta_excel"])
        tipo, _ = TipoInstitucion.objects.get_or_create(nombre="Hospital / Centro de Salud")

        for _, row in df.iterrows():
            alcaldia, _ = Alcaldia.objects.get_or_create(nombre=row["ALCALDIA"])
            Institucion.objects.update_or_create(
                clue=row["CLUE"],
                defaults={
                    "ib_clue": row["IB CLUE"],
                    "denominacion": row["DENOMINACION CLUE"],
                    "alcaldia": alcaldia,
                    "tipo": tipo
                }
            )
        self.stdout.write(self.style.SUCCESS("CLUES cargadas correctamente"))
