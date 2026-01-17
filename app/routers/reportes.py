# app/routers/reportes.py

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, aliased
from datetime import datetime

from app.database import get_db
from app.models.turno import Turno
from app.models.user import User
from app.schemas.report_schema import ReporteOut, ReporteTurno, ReporteConsumo

router = APIRouter(prefix="/reportes", tags=["Reportes"])


def parse_fecha(fecha_str: str) -> datetime:
    """
    Recibe "2025-11-20" o "20/11/2025" y lo convierte a datetime.
    """
    if "/" in fecha_str:
        d, m, y = fecha_str.split("/")
        return datetime(int(y), int(m), int(d))
    return datetime.fromisoformat(fecha_str)


def user_label(u: User | None) -> str | None:
    """
    Devuelve un nombre amigable del usuario (según campos disponibles).
    """
    if not u:
        return None
    return (
        getattr(u, "nombre", None)
        or getattr(u, "username", None)
        or getattr(u, "email", None)
        or None
    )


@router.get("/", response_model=ReporteOut)
def reporte_turnos(
    fecha_inicio: str,
    fecha_fin: str,
    mesa_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
):
    # Convertimos fechas al inicio y final del día
    fecha_inicio_dt = parse_fecha(fecha_inicio).replace(hour=0, minute=0, second=0, microsecond=0)
    fecha_fin_dt = parse_fecha(fecha_fin).replace(hour=23, minute=59, second=59, microsecond=999999)

    # Aliases para poder hacer join a users 2 veces
    UAtiende = aliased(User)
    UCobra = aliased(User)

    # Query base (solo turnos cerrados en rango por hora_fin)
    query = (
        db.query(Turno, UAtiende, UCobra)
        .outerjoin(UAtiende, Turno.atendido_por_id == UAtiende.id)
        .outerjoin(UCobra, Turno.cobrado_por_id == UCobra.id)  # <-- requiere columna cobrado_por_id
        .filter(
            Turno.hora_inicio >= fecha_inicio_dt,
            Turno.hora_fin != None,
            Turno.hora_fin <= fecha_fin_dt,
            Turno.estado == "cerrado",
        )
    )

    if mesa_id is not None:
        query = query.filter(Turno.mesa_id == mesa_id)

    rows = query.order_by(Turno.hora_inicio.asc()).all()

    turnos: list[ReporteTurno] = []
    tot_tiempo = tot_prod = tot_desc = tot_serv = tot_final = 0.0

    for (t, u_at, u_co) in rows:
        consumos = [
            ReporteConsumo(
                producto_nombre=c.producto.nombre,
                cantidad=c.cantidad,
                subtotal=c.subtotal,
            )
            for c in (t.consumos or [])
        ]

        # mesa seguro
        mesa_nombre = t.mesa.nombre if getattr(t, "mesa", None) else str(t.mesa_id)

        atendido_por = user_label(u_at)
        facturado_por = user_label(u_co)

        turnos.append(
            ReporteTurno(
                mesa=mesa_nombre,
                atendido_por=atendido_por,
                facturado_por=facturado_por,  # <-- requiere que tu schema lo tenga
                hora_inicio=t.hora_inicio,
                hora_fin=t.hora_fin,
                tiempo_total_min=int((t.hora_fin - t.hora_inicio).total_seconds() / 60),
                subtotal_tiempo=float(t.subtotal_tiempo or 0),
                subtotal_productos=float(t.subtotal_productos or 0),
                descuento=float(t.descuento or 0),
                servicios_extras=float(getattr(t, "servicios_extras", 0) or 0),
                total_final=float(t.total_final or 0),
                consumos=consumos,
            )
        )

        tot_tiempo += float(t.subtotal_tiempo or 0)
        tot_prod += float(t.subtotal_productos or 0)
        tot_desc += float(t.descuento or 0)
        tot_serv += float(getattr(t, "servicios_extras", 0) or 0)
        tot_final += float(t.total_final or 0)

    return ReporteOut(
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        mesa_id=mesa_id,
        turnos=turnos,
        total_tiempo=tot_tiempo,
        total_productos=tot_prod,
        total_descuentos=tot_desc,
        total_servicios_extras=tot_serv,
        total_general=tot_final,
    )
