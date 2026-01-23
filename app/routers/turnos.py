from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import pytz

from app.database import get_db
from app.models.turno import Turno
from app.models.consumo import Consumo
from app.models.mesa import Mesa
from app.models.producto import Producto

from app.schemas.turno_schema import (
    TurnoCreate, TurnoOut, AgregarProducto, CerrarTurno, TransferirTurno
)

from app.deps import get_current_user
from app.models.user import User


router = APIRouter(prefix="/turnos", tags=["Turnos"])

# Zona horaria Bolivia
BO = pytz.timezone("America/La_Paz")


def _now_bo():
    return datetime.now(BO).replace(tzinfo=None)

def _segundos_pausa_total(turno: Turno, ahora: datetime) -> int:
    total = int(turno.pausa_acumulada_seg or 0)

    # si existe pausa_inicio, hay pausa activa (independiente del estado)
    if turno.pausa_inicio:
        total += int((ahora - turno.pausa_inicio).total_seconds())

    return total




def _minutos_efectivos(turno: Turno, ahora: datetime, inicio: datetime | None = None) -> float:
    inicio_real = inicio or turno.hora_inicio
    total_seg = int((ahora - inicio_real).total_seconds())
    pausa_seg = _segundos_pausa_total(turno, ahora)
    efectivos = max(0, total_seg - pausa_seg)
    return efectivos / 60

def turno_to_dict(turno: Turno):
    consumos = [{
        "id": c.id,
        "producto_id": c.producto_id,
        "producto_nombre": c.producto.nombre,
        "cantidad": c.cantidad,
        "subtotal": c.subtotal
    } for c in turno.consumos]

    ahora = _now_bo()
    pausa_total = _segundos_pausa_total(turno, ahora)
    minutos_ef = _minutos_efectivos(turno, ahora)

    return {
        "id": turno.id,
        "mesa_id": turno.mesa_id,
        "hora_inicio": turno.hora_inicio,
        "hora_fin": turno.hora_fin,
        "tarifa_hora": turno.tarifa_hora,
        "subtotal_tiempo": turno.subtotal_tiempo,
        "subtotal_productos": turno.subtotal_productos,
        "servicios_extras": turno.servicios_extras,
        "descuento": turno.descuento,
        "total_final": turno.total_final,
        "estado": turno.estado,
        "pausa_inicio": turno.pausa_inicio,
        "pausa_acumulada_seg": int(turno.pausa_acumulada_seg or 0),

        # ✅ NUEVO (para ver y depurar)
        "pausa_total_seg": int(pausa_total),          # acumulada + pausa actual si está pausado
        "minutos_efectivos": float(minutos_ef),       # minutos jugados sin contar pausa

        "consumos": consumos,
    }



@router.get("/activos")
def turnos_activos(db: Session = Depends(get_db)):
    turnos = db.query(Turno).filter(Turno.estado.in_(["abierto", "pausado"])).all()
    return [turno_to_dict(t) for t in turnos]


# =======================
# INICIAR TURNO
# =======================
@router.post("/iniciar", response_model=TurnoOut)
def iniciar_turno(data: TurnoCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    mesa = db.query(Mesa).filter(Mesa.id == data.mesa_id).first()
    if not mesa:
        raise HTTPException(404, "Mesa no encontrada")

    if mesa.estado == "ocupada":
        raise HTTPException(400, "La mesa ya tiene un turno activo")

    turno = Turno(
        mesa_id=data.mesa_id,
        tarifa_hora=data.tarifa_hora,
        # 🕒 Hora correcta de Bolivia            hora_inicio=datetime.now(BO).replace(tzinfo=None),
        hora_inicio=_now_bo(),  # ✅ usa helper
        estado="abierto",
        pausa_inicio=None,  # ✅ nuevo
        pausa_acumulada_seg=0,  # ✅ nuevo
        atendido_por_id = current_user.id

    )

    db.add(turno)
    mesa.estado = "ocupada"
    mesa.hora_inicio = turno.hora_inicio
    db.commit()
    db.refresh(turno)

    return turno_to_dict(turno)


# =======================
# AGREGAR PRODUCTO
# =======================
@router.post("/{turno_id}/agregar-producto", response_model=TurnoOut)
def agregar_producto(turno_id: int, data: AgregarProducto, db: Session = Depends(get_db)):
    turno = db.query(Turno).filter(Turno.id == turno_id, Turno.estado.in_(["abierto", "pausado"])).first()
    if not turno:
        raise HTTPException(status_code=404, detail="Turno no encontrado o ya cerrado")

    producto = db.query(Producto).filter(Producto.id == data.producto_id).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    # ✅ stock correcto
    if producto.cantidad < data.cantidad:
        raise HTTPException(status_code=400, detail="Stock insuficiente")

    # ✅ precio correcto (venta)
    subtotal = producto.precio_venta * data.cantidad

    consumo = Consumo(
        turno_id=turno.id,
        producto_id=producto.id,
        cantidad=data.cantidad,
        subtotal=subtotal
    )

    # ✅ descontar cantidad
    producto.cantidad -= data.cantidad
    turno.subtotal_productos += subtotal

    db.add(consumo)
    db.commit()
    db.refresh(turno)

    return turno_to_dict(turno)

# =======================
# PREVIEW ANTES DE CERRAR
# =======================
@router.get("/{turno_id}/preview", response_model=TurnoOut)
def preview(turno_id: int, db: Session = Depends(get_db)):
    turno = db.query(Turno).filter(Turno.id == turno_id).first()
    if not turno:
        raise HTTPException(404, "Turno no encontrado")

    # =============================
    # Normalizar hora_inicio
    # =============================
    inicio = turno.hora_inicio

    if isinstance(inicio, str):
        try:
            inicio = datetime.strptime(inicio, "%Y-%m-%d %H:%M:%S")
        except:
            raise HTTPException(500, "Error interno: hora_inicio inválida")

    ahora = _now_bo()

    # usamos inicio local para evitar errores si era string
    minutos = _minutos_efectivos(turno, ahora, inicio=inicio)


    # =============================
    # Calcular subtotal tiempo
    # =============================
    if minutos <= 30:
        subtotal = turno.tarifa_hora / 2
    else:
        horas_completas = int(minutos // 60)
        resto = minutos % 60

        subtotal = horas_completas * turno.tarifa_hora
        subtotal += turno.tarifa_hora if resto >= 31 else turno.tarifa_hora / 2

    turno.subtotal_tiempo = subtotal
    turno.total_final = subtotal + turno.subtotal_productos + turno.servicios_extras - turno.descuento

    return turno_to_dict(turno)



# =======================
# CERRAR TURNO
# =======================
@router.patch("/{turno_id}/cerrar", response_model=TurnoOut)
def cerrar_turno(
    turno_id: int,
    data: CerrarTurno,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),  # ✅ NUEVO
):
    turno = db.query(Turno).filter(
        Turno.id == turno_id,
        Turno.estado.in_(["abierto", "pausado"])
    ).first()
    if not turno:
        raise HTTPException(404, "Turno no encontrado o ya cerrado")

    turno.hora_fin = _now_bo()

    if turno.pausa_inicio:
        delta = int((turno.hora_fin - turno.pausa_inicio).total_seconds())
        turno.pausa_acumulada_seg = int(turno.pausa_acumulada_seg or 0) + max(0, delta)
        turno.pausa_inicio = None

    minutos = _minutos_efectivos(turno, turno.hora_fin)

    if minutos <= 30:
        subtotal = (turno.tarifa_hora / 2)
    else:
        horas_completas = int(minutos // 60)
        resto = minutos % 60

        subtotal = horas_completas * turno.tarifa_hora
        subtotal += turno.tarifa_hora if resto >= 31 else turno.tarifa_hora / 2

    turno.subtotal_tiempo = subtotal
    turno.descuento = data.descuento
    turno.servicios_extras = data.servicios_extras

    turno.total_final = subtotal + turno.subtotal_productos + turno.servicios_extras - turno.descuento
    turno.estado = "cerrado"

    # ✅ NUEVO: guardamos quién cerró/cobró
    turno.cobrado_por_id = current_user.id

    mesa = db.query(Mesa).filter(Mesa.id == turno.mesa_id).first()
    mesa.estado = "libre"
    mesa.hora_inicio = None

    db.commit()
    db.refresh(turno)

    return turno_to_dict(turno)




# =======================
# PAUSAR TURNO
# =======================
@router.patch("/{turno_id}/pausar", response_model=TurnoOut)
def pausar_turno(
    turno_id: int,
    db: Session = Depends(get_db),
):
    turno = db.query(Turno).filter(
        Turno.id == turno_id,
        Turno.estado.in_(["abierto", "pausado"])
    ).first()
    if not turno:
        raise HTTPException(404, "Turno no encontrado o ya cerrado")

    # idempotente
    if turno.pausa_inicio:
        turno.estado = "pausado"  # por si estaba desincronizado
        return turno_to_dict(turno)

    turno.estado = "pausado"
    turno.pausa_inicio = _now_bo()

    db.commit()
    db.refresh(turno)
    return turno_to_dict(turno)


# =======================
# REANUDAR TURNO
# =======================
@router.patch("/{turno_id}/reanudar", response_model=TurnoOut)
def reanudar_turno(
    turno_id: int,
    db: Session = Depends(get_db),
):
    turno = db.query(Turno).filter(
        Turno.id == turno_id,
        Turno.estado.in_(["abierto", "pausado"])
    ).first()
    if not turno:
        raise HTTPException(404, "Turno no encontrado o ya cerrado")

    if not turno.pausa_inicio:
        turno.estado = "abierto"
        db.commit()
        db.refresh(turno)
        return turno_to_dict(turno)

    ahora = _now_bo()
    delta = int((ahora - turno.pausa_inicio).total_seconds())
    turno.pausa_acumulada_seg = int(turno.pausa_acumulada_seg or 0) + max(0, delta)
    turno.pausa_inicio = None
    turno.estado = "abierto"

    db.commit()
    db.refresh(turno)
    return turno_to_dict(turno)



# =======================
# TRANSFERIR TURNO
# =======================
@router.patch("/transferir/{mesa_origen_id}")
def transferir_turno(
    mesa_origen_id: int,
    data: TransferirTurno,
    db: Session = Depends(get_db)
):
    mesa_destino_id = data.mesa_destino_id

    if mesa_origen_id == mesa_destino_id:
        raise HTTPException(status_code=400, detail="Mesa destino no puede ser igual a mesa origen")

    # 1) Turno activo en mesa origen (abierto O pausado)
    turno = db.query(Turno).filter(
        Turno.mesa_id == mesa_origen_id,
        Turno.estado.in_(["abierto", "pausado"])
    ).first()

    if not turno:
        raise HTTPException(status_code=404, detail="No hay turno activo (abierto/pausado) en la mesa origen")

    # 2) Validar mesas
    mesa_origen = db.query(Mesa).filter(Mesa.id == mesa_origen_id).first()
    if not mesa_origen:
        raise HTTPException(status_code=404, detail="Mesa origen no encontrada")

    mesa_destino = db.query(Mesa).filter(Mesa.id == mesa_destino_id).first()
    if not mesa_destino:
        raise HTTPException(status_code=404, detail="Mesa destino no encontrada")

    # 3) Mesa destino debe estar libre (y sin turno activo)
    if mesa_destino.estado == "ocupada":
        raise HTTPException(status_code=400, detail="La mesa destino ya está ocupada")

    turno_destino = db.query(Turno).filter(
        Turno.mesa_id == mesa_destino_id,
        Turno.estado.in_(["abierto", "pausado"])
    ).first()
    if turno_destino:
        raise HTTPException(status_code=400, detail="La mesa destino ya tiene un turno activo")

    # 4) Transferencia (mover turno + estados de mesas)
    try:
        turno.mesa_id = mesa_destino_id

        mesa_origen.estado = "libre"
        mesa_origen.hora_inicio = None

        mesa_destino.estado = "ocupada"
        mesa_destino.hora_inicio = turno.hora_inicio  # mantiene el inicio real (pausas se descuentan en backend)

        db.commit()
        db.refresh(turno)

        return {
            "mensaje": "Turno transferido",
            "turno_id": turno.id,
            "mesa_origen_id": mesa_origen_id,
            "mesa_destino_id": mesa_destino_id,
        }
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error al transferir el turno")


