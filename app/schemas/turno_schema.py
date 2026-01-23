from pydantic import BaseModel
from datetime import datetime
from typing import List

class ConsumoDetalle(BaseModel):
    id: int
    producto_id: int
    producto_nombre: str
    cantidad: int
    subtotal: float

    class Config:
        from_attributes = True


class TurnoBase(BaseModel):
    mesa_id: int
    tarifa_hora: float


class TurnoCreate(TurnoBase):
    pass


class AgregarProducto(BaseModel):
    producto_id: int
    cantidad: int


class CerrarTurno(BaseModel):
    descuento: float = 0
    servicios_extras: float = 0  # 👈 NUEVO

class TransferirTurno(BaseModel):
    mesa_destino_id: int


class TurnoOut(BaseModel):
    id: int
    mesa_id: int
    hora_inicio: datetime
    hora_fin: datetime | None
    tarifa_hora: float

    subtotal_tiempo: float
    subtotal_productos: float
    servicios_extras: float
    descuento: float
    total_final: float
    estado: str

    pausa_inicio: datetime | None = None
    pausa_acumulada_seg: int = 0

    consumos: List[ConsumoDetalle] = []

    class Config:
        from_attributes = True
