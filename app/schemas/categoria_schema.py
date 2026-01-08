from pydantic import BaseModel, Field

class CategoriaBase(BaseModel):
    nombre: str = Field(min_length=1, max_length=50)

class CategoriaCreate(CategoriaBase):
    pass

class CategoriaUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=50)

class CategoriaOut(CategoriaBase):
    id: int

    class Config:
        from_attributes = True
