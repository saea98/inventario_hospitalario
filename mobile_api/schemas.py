from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class ConteoRequest(BaseModel):
    cantidad_fisica: int = Field(..., ge=0)
    fecha_caducidad: Optional[date] = None
    observaciones: str = ''


class CrearLoteRequest(BaseModel):
    clave_cnis: str
    numero_lote: str
    cantidad_inicial: int = Field(..., ge=0)
    fecha_caducidad: date
    precio_unitario: Optional[float] = None
    observaciones: str = ''
