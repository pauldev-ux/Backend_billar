from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import pytz

from app.database import get_db
from app.models.gasto import Gasto
from app.schemas.gasto_schema import GastoCreate, GastoOut

from app.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/gastos", tags=["Gastos"])
BO = pytz.timezone("America/La_Paz")

def require_admin(current_user: User):
    if getattr(current_user, "rol", None) != "admin":
        raise HTTPException(status_code=403, detail="Solo admin")

@router.get("/", response_model=list[GastoOut])
def listar_gastos(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_admin(current_user)
    return db.query(Gasto).order_by(Gasto.created_at.desc()).all()

@router.post("/", response_model=GastoOut)
def crear_gasto(
    data: GastoCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_admin(current_user)

    precio = float(data.precio or 0)
    cantidad = int(data.cantidad or 0)
    if cantidad <= 0:
        raise HTTPException(400, "cantidad debe ser mayor a 0")
    if precio < 0:
        raise HTTPException(400, "precio no puede ser negativo")

    total = precio * cantidad

    gasto = Gasto(
        nombre=data.nombre,
        precio=precio,
        cantidad=cantidad,
        total=total,
        created_at=datetime.now(BO).replace(tzinfo=None),
    )
    db.add(gasto)
    db.commit()
    db.refresh(gasto)
    return gasto
