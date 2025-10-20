import pandas as pd
from django.core.management.base import BaseCommand
from inventario.models import UbicacionAlmacen, Almacen, Institucion

class Command(BaseCommand):
    help = "Carga masiva de ubicaciones desde un Excel"

    def add_arguments(self, parser):
        parser.add_argument('archivo', type=str, help='Ruta del archivo Excel o CSV')

    def handle(self, *args, **kwargs):
        archivo = kwargs['archivo']
        self.stdout.write(f"Procesando archivo: {archivo}")

        # Lee el Excel (o CSV)
        try:
            df = pd.read_excel(archivo)
        except Exception:
            df = pd.read_csv(archivo)

        # Columnas esperadas: clue, ib_clue, RACK, POSICION, NIVEL, UBICACION, AREA
        for idx, row in df.iterrows():
            clue = row['clue']
            ib_clue = row['ib_clue']
            rack = str(row['RACK'])
            posicion = str(row['POSICION']).zfill(2)
            nivel = str(row['NIVEL']).zfill(2)
            ubicacion_codigo = f"{rack}.{posicion}.{nivel}"
            area = row.get('AREA', '')

            # Obtener institución
            institucion = Institucion.objects.filter(clue=clue, ib_clue=ib_clue).first()
            if not institucion:
                self.stdout.write(f"❌ Institución no encontrada para CLUE={clue} IB_CLUE={ib_clue}")
                continue

            # Suponemos que existe un almacén por institución, si no se puede crear
            almacen, _ = Almacen.objects.get_or_create(nombre=f"Almacén {institucion.denominacion}", institucion=institucion)

            # Crear o actualizar la ubicación
            ubicacion, created = UbicacionAlmacen.objects.update_or_create(
                almacen=almacen,
                codigo=ubicacion_codigo,
                defaults={
                    'rack': rack,
                    'pasillo': posicion,
                    'nivel': nivel,
                    'descripcion': row.get('UBICACIÓN', ''),
                    'activo': True
                }
            )

            if created:
                self.stdout.write(f"✅ Ubicación creada: {ubicacion_codigo} en {almacen.nombre}")
            else:
                self.stdout.write(f"⚡ Ubicación actualizada: {ubicacion_codigo} en {almacen.nombre}")

        self.stdout.write(self.style.SUCCESS("Carga masiva finalizada."))
