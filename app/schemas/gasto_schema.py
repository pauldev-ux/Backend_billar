from pydantic import BaseModel
from datetime import datetime

class GastoCreate(BaseModel):
    nombre: str
    precio: float
    cantidad: int = 1

class GastoOut(BaseModel):
    id: int
    nombre: str
    precio: float
    cantidad: int
    total: float
    created_at: datetime

    class Config:
        from_attributes = True
