from pydantic import BaseModel, Field
from app.schemas.categoria_schema import CategoriaOut

class ProductoBase(BaseModel):
    nombre: str
    precio_compra: float = Field(ge=0)
    precio_venta: float = Field(ge=0)
    cantidad: int = Field(ge=0)
    imagen: str | None = None  # URL o path
    categoria_id: int | None = None


class ProductoCreate(ProductoBase):
    pass


class ProductoUpdate(BaseModel):
    nombre: str | None = None
    precio_compra: float | None = Field(default=None, ge=0)
    precio_venta: float | None = Field(default=None, ge=0)
    cantidad: int | None = Field(default=None, ge=0)
    imagen: str | None = None
    categoria_id: int | None = None


# (Opcional pro) Ajuste de stock por delta
class ProductoStockDelta(BaseModel):
    delta: int  # puede ser + o -


class ProductoOut(ProductoBase):
    id: int
    categoria: CategoriaOut | None = None

    class Config:
        from_attributes = True
