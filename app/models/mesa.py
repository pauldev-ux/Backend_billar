from sqlalchemy import Column, Integer, String, DateTime, Float
from app.database import Base

class Mesa(Base):
    __tablename__ = "mesas"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    tarifa_por_hora = Column(Float, nullable=True)

    estado = Column(String, default="libre")
    hora_inicio = Column(DateTime, nullable=True)
    hora_fin = Column(DateTime, nullable=True)

    imagen = Column(String, nullable=True)
