"""
Carga de almacenes centrales nacionales desde el formato de
actualización/ratificación (Excel), sin cambiar estructura de tablas.

Reglas acordadas:
- Conservar ambos CLUE: SALUD → Institucion.clue, IMSS-B → Institucion.ib_clue
- Si CLUE SALUD es N/A, usar CLUE IMSS-B como clue (e ib_clue)
- Código de almacén: NAC-{CLUE}
- Nombre de almacén: "{Entidad} - {Unidad}"
- Existentes: solo rellenar nombre/dirección si están vacíos
- Solo filas de almacenes centrales del Excel (hoja Almacenes)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import BinaryIO, Iterable, List, Optional, Union

import openpyxl
from django.db import transaction

from .models import Almacen, Institucion, TipoInstitucion

HOJA_ALMACENES = 'Almacenes '
FILA_DATOS_INICIO = 13  # 1-based; encabezados en 11-12
NA_VALUES = {'', 'N/A', 'NA', 'NONE', 'NULL', '-'}


def _celda_texto(valor) -> str:
    if valor is None:
        return ''
    return str(valor).strip()


def _es_na(valor: str) -> bool:
    return _celda_texto(valor).upper() in NA_VALUES


def _vacio(valor: Optional[str]) -> bool:
    return valor is None or not str(valor).strip()


@dataclass
class FilaAlmacenCentral:
    linea: int
    entidad: str
    clue_salud: str
    clue_imssb: str
    unidad: str
    direccion: str

    @property
    def clue_principal(self) -> Optional[str]:
        if not _es_na(self.clue_salud):
            return self.clue_salud[:20]
        if not _es_na(self.clue_imssb):
            return self.clue_imssb[:20]
        return None

    @property
    def ib_clue(self) -> Optional[str]:
        if _es_na(self.clue_imssb):
            # Si la clave principal vino del IMSS-B (SALUD era N/A), conservar ambas iguales
            if _es_na(self.clue_salud) and self.clue_principal:
                return self.clue_principal
            return None
        return self.clue_imssb[:20]

    @property
    def codigo_almacen(self) -> Optional[str]:
        clue = self.clue_principal
        return f'NAC-{clue}' if clue else None

    @property
    def nombre_almacen(self) -> str:
        return f'{self.entidad} - {self.unidad}'[:150]

    @property
    def denominacion(self) -> str:
        return self.unidad[:200]


@dataclass
class AccionCarga:
    tipo: str  # crear_institucion | actualizar_institucion | omitir_institucion | crear_almacen | actualizar_almacen | omitir_almacen | error
    mensaje: str
    fila: Optional[FilaAlmacenCentral] = None


@dataclass
class ResultadoCarga:
    acciones: List[AccionCarga] = field(default_factory=list)
    filas_leidas: int = 0
    errores: int = 0
    instituciones_crear: int = 0
    instituciones_actualizar: int = 0
    almacenes_crear: int = 0
    almacenes_actualizar: int = 0
    omitidos: int = 0

    def registrar(self, accion: AccionCarga):
        self.acciones.append(accion)
        if accion.tipo == 'error':
            self.errores += 1
        elif accion.tipo == 'crear_institucion':
            self.instituciones_crear += 1
        elif accion.tipo == 'actualizar_institucion':
            self.instituciones_actualizar += 1
        elif accion.tipo == 'crear_almacen':
            self.almacenes_crear += 1
        elif accion.tipo == 'actualizar_almacen':
            self.almacenes_actualizar += 1
        elif accion.tipo in ('omitir_institucion', 'omitir_almacen'):
            self.omitidos += 1


def leer_filas_excel(fuente: Union[str, Path, BinaryIO]) -> List[FilaAlmacenCentral]:
    """Lee la hoja de almacenes centrales del formato oficial."""
    wb = openpyxl.load_workbook(fuente, data_only=True, read_only=True)
    try:
        nombre_hoja = None
        for s in wb.sheetnames:
            if s.strip().lower().startswith('almacenes'):
                nombre_hoja = s
                break
        if not nombre_hoja:
            raise ValueError(
                f"No se encontró hoja 'Almacenes'. Hojas: {wb.sheetnames}"
            )
        ws = wb[nombre_hoja]
        filas: List[FilaAlmacenCentral] = []
        for i, row in enumerate(ws.iter_rows(min_row=FILA_DATOS_INICIO, values_only=True), start=FILA_DATOS_INICIO):
            entidad = _celda_texto(row[0] if len(row) > 0 else None)
            clue_salud = _celda_texto(row[1] if len(row) > 1 else None)
            clue_imssb = _celda_texto(row[2] if len(row) > 2 else None)
            unidad = _celda_texto(row[3] if len(row) > 3 else None)
            direccion = _celda_texto(row[4] if len(row) > 4 else None)
            if not entidad and not clue_salud and not unidad:
                continue
            filas.append(
                FilaAlmacenCentral(
                    linea=i,
                    entidad=entidad,
                    clue_salud=clue_salud,
                    clue_imssb=clue_imssb,
                    unidad=unidad,
                    direccion=direccion,
                )
            )
        return filas
    finally:
        wb.close()


def _tipo_institucion_default() -> TipoInstitucion:
    tipo = TipoInstitucion.objects.order_by('id').first()
    if not tipo:
        tipo = TipoInstitucion.objects.create(tipo='OTRO', descripcion='Almacén central')
    return tipo


def _campos_institucion_a_rellenar(inst: Institucion, fila: FilaAlmacenCentral) -> dict:
    """Solo rellena nombre/denominación/dirección/estado/ib_clue si faltan."""
    cambios = {}
    if _vacio(inst.denominacion) and fila.denominacion:
        cambios['denominacion'] = fila.denominacion
    if _vacio(inst.nombre) and fila.denominacion:
        cambios['nombre'] = fila.denominacion
    if _vacio(inst.direccion) and fila.direccion:
        cambios['direccion'] = fila.direccion
    if _vacio(inst.estado) and fila.entidad:
        cambios['estado'] = fila.entidad
    # Conservar IB CLUE si aún no está capturado
    if _vacio(inst.ib_clue) and fila.ib_clue:
        # Evitar choque de unique si otro registro ya tiene ese ib_clue
        conflicto = (
            Institucion.objects.filter(ib_clue=fila.ib_clue)
            .exclude(pk=inst.pk)
            .exists()
        )
        if not conflicto:
            cambios['ib_clue'] = fila.ib_clue
    return cambios


def _campos_almacen_a_rellenar(almacen: Almacen, fila: FilaAlmacenCentral) -> dict:
    cambios = {}
    if _vacio(almacen.nombre) and fila.nombre_almacen:
        cambios['nombre'] = fila.nombre_almacen
    if _vacio(almacen.direccion) and fila.direccion:
        cambios['direccion'] = fila.direccion
    return cambios


def procesar_almacenes_centrales(
    filas: Iterable[FilaAlmacenCentral],
    *,
    dry_run: bool = True,
) -> ResultadoCarga:
    """
    Aplica (o simula) la carga. dry_run=True no escribe en BD.
    """
    resultado = ResultadoCarga()
    tipo = None if dry_run else _tipo_institucion_default()

    def _run():
        for fila in filas:
            resultado.filas_leidas += 1
            clue = fila.clue_principal
            if not clue:
                resultado.registrar(AccionCarga(
                    'error',
                    f"Fila {fila.linea}: sin CLUE SALUD ni IMSS-B válidos.",
                    fila,
                ))
                continue
            if not fila.unidad:
                resultado.registrar(AccionCarga(
                    'error',
                    f"Fila {fila.linea} ({clue}): falta Unidad.",
                    fila,
                ))
                continue
            if not fila.entidad:
                resultado.registrar(AccionCarga(
                    'error',
                    f"Fila {fila.linea} ({clue}): falta Entidad.",
                    fila,
                ))
                continue

            codigo = fila.codigo_almacen
            ib = fila.ib_clue

            # --- Institución ---
            inst = Institucion.objects.filter(clue=clue).first()
            if inst is None:
                # ib_clue unique: si otro lo tiene, crear sin ib o error
                if ib and Institucion.objects.filter(ib_clue=ib).exists():
                    resultado.registrar(AccionCarga(
                        'error',
                        f"Fila {fila.linea}: ib_clue {ib} ya usado por otra institución.",
                        fila,
                    ))
                    continue
                resultado.registrar(AccionCarga(
                    'crear_institucion',
                    f"Crear Institucion clue={clue} ib_clue={ib or '—'} "
                    f"denominacion={fila.denominacion!r} estado={fila.entidad!r}",
                    fila,
                ))
                if not dry_run:
                    inst = Institucion.objects.create(
                        clue=clue,
                        ib_clue=ib,
                        denominacion=fila.denominacion,
                        nombre=fila.denominacion,
                        estado=fila.entidad,
                        direccion=fila.direccion or None,
                        tipo_institucion=tipo,
                        activo=True,
                    )
            else:
                cambios = _campos_institucion_a_rellenar(inst, fila)
                if cambios:
                    resultado.registrar(AccionCarga(
                        'actualizar_institucion',
                        f"Actualizar Institucion {clue}: {cambios}",
                        fila,
                    ))
                    if not dry_run:
                        for k, v in cambios.items():
                            setattr(inst, k, v)
                        inst.save(update_fields=list(cambios.keys()) + ['fecha_actualizacion'])
                else:
                    resultado.registrar(AccionCarga(
                        'omitir_institucion',
                        f"Institucion {clue} ya tiene nombre/dirección (sin cambios).",
                        fila,
                    ))
                if dry_run:
                    # para enlazar almacén en dry-run usamos el objeto existente
                    pass

            if dry_run and inst is None:
                # Simulación: no hay PK; igual reportamos almacén
                resultado.registrar(AccionCarga(
                    'crear_almacen',
                    f"Crear Almacen codigo={codigo} nombre={fila.nombre_almacen!r} "
                    f"(institucion nueva {clue})",
                    fila,
                ))
                continue

            if inst is None:
                # Error previo al crear
                continue

            # --- Almacén ---
            almacen = Almacen.objects.filter(codigo=codigo).first()
            if almacen is None:
                resultado.registrar(AccionCarga(
                    'crear_almacen',
                    f"Crear Almacen codigo={codigo} nombre={fila.nombre_almacen!r} "
                    f"institucion={clue}",
                    fila,
                ))
                if not dry_run:
                    Almacen.objects.create(
                        institucion=inst,
                        nombre=fila.nombre_almacen,
                        codigo=codigo,
                        direccion=fila.direccion or None,
                        activo=True,
                    )
            else:
                cambios_a = _campos_almacen_a_rellenar(almacen, fila)
                if cambios_a:
                    resultado.registrar(AccionCarga(
                        'actualizar_almacen',
                        f"Actualizar Almacen {codigo}: {cambios_a}",
                        fila,
                    ))
                    if not dry_run:
                        for k, v in cambios_a.items():
                            setattr(almacen, k, v)
                        almacen.save(update_fields=list(cambios_a.keys()))
                else:
                    resultado.registrar(AccionCarga(
                        'omitir_almacen',
                        f"Almacen {codigo} ya tiene nombre/dirección (sin cambios).",
                        fila,
                    ))

    if dry_run:
        _run()
    else:
        with transaction.atomic():
            _run()

    return resultado
