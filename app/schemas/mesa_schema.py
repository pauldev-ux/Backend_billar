from pydantic import BaseModel
from datetime import datetime

class MesaBase(BaseModel):
    nombre: str
    tarifa_por_hora: float
    tipo_tiempo: str = "limitado"
    tiempo_default_min: int = 60
    imagen: str | None = None

class MesaCreate(MesaBase):
    pass

class MesaUpdate(BaseModel):
    estado: str | None = None
    hora_inicio: datetime | None = None
    hora_fin: datetime | None = None
    imagen: str | None = None

class MesaOut(BaseModel):
    id: int
    nombre: str
    tarifa_por_hora: float
    estado: str

    hora_inicio: datetime | None = None
    turno_activo: int | None = None
    turno_estado: str | None = None

    # ✅ NUEVOS (para pausa / cronómetro)
    pausa_inicio: datetime | None = None
    pausa_acumulada_seg: int = 0

    imagen: str | None = None

    class Config:
        from_attributes = True

