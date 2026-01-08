from sqlalchemy import Column, Integer, String, Float, ForeignKey
from app.database import Base
from sqlalchemy.orm import relationship

class Producto(Base):
    __tablename__ = "productos"

    id = Column(Integer, primary_key=True, index=True)

    nombre = Column(String, nullable=False)

    precio_compra = Column(Float, nullable=False)
    precio_venta = Column(Float, nullable=False)

    cantidad = Column(Integer, nullable=False, default=0)

    # Guarda URL o ruta. Permite null por si no tiene imagen.
    imagen = Column(String, nullable=True)

    # categoria
    categoria_id = Column(Integer, ForeignKey("categorias.id"), nullable=True)
    categoria = relationship("Categoria")
