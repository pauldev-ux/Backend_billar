from sqlalchemy import Column, Integer, DateTime, Float, String, ForeignKey
from datetime import datetime
import pytz
from app.database import Base

BO = pytz.timezone("America/La_Paz")

class ArqueoCaja(Base):
    __tablename__ = "arqueos_caja"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    fecha_inicio = Column(DateTime, nullable=False)
    fecha_fin = Column(DateTime, nullable=False)

    total_tiempo = Column(Float, default=0)
    total_productos = Column(Float, default=0)
    total_descuentos = Column(Float, default=0)
    total_servicios_extras = Column(Float, default=0)
    total_general = Column(Float, default=0)

    monto_retirado = Column(Float, default=0)
    monto_cambio = Column(Float, default=0)

    observacion = Column(String, nullable=True)

    creado_en = Column(DateTime, default=lambda: datetime.now(BO).replace(tzinfo=None))
