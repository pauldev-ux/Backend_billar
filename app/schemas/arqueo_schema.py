from pydantic import BaseModel, Field
from datetime import datetime

class ArqueoCreate(BaseModel):
    fecha_inicio: str
    fecha_fin: str
    monto_retirado: float = Field(ge=0)
    monto_cambio: float = Field(ge=0)
    observacion: str | None = None

class ArqueoOut(BaseModel):
    id: int
    usuario_id: int
    fecha_inicio: datetime
    fecha_fin: datetime

    total_tiempo: float
    total_productos: float
    total_descuentos: float
    total_servicios_extras: float
    total_general: float

    monto_retirado: float
    monto_cambio: float
    observacion: str | None = None
    creado_en: datetime

    class Config:
        from_attributes = True
