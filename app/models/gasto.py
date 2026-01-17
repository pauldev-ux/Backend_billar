from sqlalchemy import Column, Integer, String, Float, DateTime
from app.database import Base
from datetime import datetime
import pytz

BO = pytz.timezone("America/La_Paz")

class Gasto(Base):
    __tablename__ = "gastos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    precio = Column(Float, nullable=False, default=0)
    cantidad = Column(Integer, nullable=False, default=1)
    total = Column(Float, nullable=False, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(BO).replace(tzinfo=None))
