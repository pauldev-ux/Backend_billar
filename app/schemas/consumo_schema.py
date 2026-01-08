from pydantic import BaseModel

class ConsumoBase(BaseModel):
    turno_id: int
    producto_id: int
    cantidad: int

class ConsumoCreate(ConsumoBase):
    pass

class ConsumoOut(BaseModel):
    id: int
    turno_id: int
    producto_id: int
    cantidad: int
    subtotal: float

    class Config:
        from_attributes = True

