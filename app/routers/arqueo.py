from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import get_db
from app.models.turno import Turno
from app.models.arqueo_caja import ArqueoCaja
from app.schemas.arqueo_schema import ArqueoCreate, ArqueoOut
from fastapi import Query

from app.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/arqueo", tags=["Arqueo"])

def parse_fecha(fecha_str: str):
    if "/" in fecha_str:
        d, m, y = fecha_str.split("/")
        return datetime(int(y), int(m), int(d))
    return datetime.fromisoformat(fecha_str)

@router.post("/cerrar", response_model=ArqueoOut)
def cerrar_arqueo(
    data: ArqueoCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    fecha_inicio_dt = parse_fecha(data.fecha_inicio).replace(hour=0, minute=0, second=0)
    fecha_fin_dt = parse_fecha(data.fecha_fin).replace(hour=23, minute=59, second=59)

    turnos_db = db.query(Turno).filter(
        Turno.hora_inicio >= fecha_inicio_dt,
        Turno.hora_fin != None,
        Turno.hora_fin <= fecha_fin_dt,
        Turno.estado == "cerrado",
        Turno.atendido_por_id == current_user.id
    ).all()

    if not turnos_db:
        raise HTTPException(status_code=400, detail="No hay turnos cerrados en ese rango para este usuario")

    tot_tiempo = tot_prod = tot_desc = tot_serv = tot_final = 0.0

    for t in turnos_db:
        tot_tiempo += t.subtotal_tiempo
        tot_prod += t.subtotal_productos
        tot_desc += t.descuento
        tot_serv += getattr(t, "servicios_extras", 0)
        tot_final += t.total_final

    arqueo = ArqueoCaja(
        usuario_id=current_user.id,
        fecha_inicio=fecha_inicio_dt,
        fecha_fin=fecha_fin_dt,
        total_tiempo=tot_tiempo,
        total_productos=tot_prod,
        total_descuentos=tot_desc,
        total_servicios_extras=tot_serv,
        total_general=tot_final,
        monto_retirado=data.monto_retirado,
        monto_cambio=data.monto_cambio,
        observacion=data.observacion
    )

    db.add(arqueo)
    db.commit()
    db.refresh(arqueo)
    return arqueo
