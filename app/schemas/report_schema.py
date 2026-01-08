from pydantic import BaseModel
from typing import List
from datetime import datetime

class ReporteConsumo(BaseModel):
    producto_nombre: str
    cantidad: int
    subtotal: float

class ReporteTurno(BaseModel):
    mesa: str
    atendido_por: str | None = None  # 👈 NUEVO
    hora_inicio: datetime
    hora_fin: datetime
    tiempo_total_min: int
    subtotal_tiempo: float
    subtotal_productos: float
    descuento: float
    servicios_extras: float
    total_final: float
    consumos: List[ReporteConsumo]

class ReporteOut(BaseModel):
    fecha_inicio: str
    fecha_fin: str
    mesa_id: int | None
    turnos: List[ReporteTurno]

    total_tiempo: float
    total_productos: float
    total_descuentos: float
    total_servicios_extras: float
    total_general: float
