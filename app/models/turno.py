from sqlalchemy import Column, Integer, ForeignKey, DateTime, Float, String
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
import pytz

# Zona horaria Bolivia
BO = pytz.timezone("America/La_Paz")

class Turno(Base):
    __tablename__ = "turnos"

    id = Column(Integer, primary_key=True, index=True)
    mesa_id = Column(Integer, ForeignKey("mesas.id"))

    # Hora boliviana por defecto
    hora_inicio = Column(DateTime, default=lambda: datetime.now(BO))
    hora_fin = Column(DateTime, nullable=True)

    tarifa_hora = Column(Float, nullable=False)

    subtotal_tiempo = Column(Float, default=0)
    subtotal_productos = Column(Float, default=0)

    servicios_extras = Column(Float, default=0)

    descuento = Column(Float, default=0)

    total_final = Column(Float, default=0)
    estado = Column(String, default="abierto")

    mesa = relationship("Mesa", backref="turnos")
    consumos = relationship("Consumo", back_populates="turno")

    #relaciones entre tabla de users
    atendido_por_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    cobrado_por_id = Column(Integer, ForeignKey("users.id"), nullable=True)

