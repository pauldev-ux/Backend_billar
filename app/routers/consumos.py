from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.consumo import Consumo
from app.models.turno import Turno
from app.models.producto import Producto
from app.schemas.consumo_schema import ConsumoCreate, ConsumoOut

router = APIRouter(prefix="/consumos", tags=["Consumos"])


# =========================
# REGISTRAR CONSUMO
# =========================
@router.post("/", response_model=ConsumoOut)
def registrar_consumo(data: ConsumoCreate, db: Session = Depends(get_db)):
    # 🔎 Validar turno
    turno = db.query(Turno).filter(
        Turno.id == data.turno_id,
        Turno.estado == "abierto"
    ).first()
    if not turno:
        raise HTTPException(status_code=404, detail="Turno no encontrado o cerrado")

    # 🔎 Validar producto
    producto = db.query(Producto).filter(Producto.id == data.producto_id).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    # ✅ Validar cantidad disponible
    if producto.cantidad < data.cantidad:
        raise HTTPException(status_code=400, detail="Stock insuficiente")

    # ✅ Usar PRECIO DE VENTA
    subtotal = producto.precio_venta * data.cantidad

    consumo = Consumo(
        turno_id=data.turno_id,
        producto_id=data.producto_id,
        cantidad=data.cantidad,
        subtotal=subtotal
    )

    # ✅ Descontar inventario
    producto.cantidad -= data.cantidad

    # ✅ Actualizar subtotal del turno
    turno.subtotal_productos += subtotal

    db.add(consumo)
    db.commit()
    db.refresh(consumo)

    return consumo


# =========================
# LISTAR CONSUMOS POR TURNO
# =========================
@router.get("/turno/{turno_id}", response_model=list[ConsumoOut])
def obtener_consumos(turno_id: int, db: Session = Depends(get_db)):
    return db.query(Consumo).filter(Consumo.turno_id == turno_id).all()


# =========================
# ELIMINAR CONSUMO
# =========================
@router.delete("/{consumo_id}")
def eliminar_consumo(consumo_id: int, db: Session = Depends(get_db)):
    consumo = db.query(Consumo).filter(Consumo.id == consumo_id).first()
    if not consumo:
        raise HTTPException(status_code=404, detail="Consumo no encontrado")

    # (opcional pro) devolver stock al eliminar consumo
    producto = db.query(Producto).filter(Producto.id == consumo.producto_id).first()
    if producto:
        producto.cantidad += consumo.cantidad

    db.delete(consumo)
    db.commit()
    return {"mensaje": "Consumo eliminado"}
