from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.mesa import Mesa
from app.models.turno import Turno
from app.schemas.mesa_schema import MesaCreate, MesaUpdate, MesaOut

from pathlib import Path
from uuid import uuid4

router = APIRouter(prefix="/mesas", tags=["Mesas"])


# ✅ Crear mesa normal (JSON) - NO SE ROMPE
@router.post("/", response_model=MesaOut)
def create_mesa(data: MesaCreate, db: Session = Depends(get_db)):
    mesa = Mesa(
        nombre=data.nombre,
        tarifa_por_hora=data.tarifa_por_hora,
        estado="libre",
        imagen=data.imagen  # si llega como string, también sirve
    )
    db.add(mesa)
    db.commit()
    db.refresh(mesa)
    return mesa


# ✅ Crear mesa con imagen (multipart/form-data)
@router.post("/con-imagen", response_model=MesaOut)
def create_mesa_con_imagen(
    nombre: str = Form(...),
    tarifa_por_hora: float = Form(...),
    imagen: UploadFile | None = File(None),
    db: Session = Depends(get_db)
):
    imagen_url = None

    if imagen:
        uploads_dir = Path(__file__).resolve().parents[1] / "static" / "uploads" / "mesas"
        uploads_dir.mkdir(parents=True, exist_ok=True)

        ext = Path(imagen.filename).suffix.lower()
        if ext not in [".jpg", ".jpeg", ".png", ".webp"]:
            raise HTTPException(status_code=400, detail="Formato de imagen no permitido")

        filename = f"{uuid4().hex}{ext}"
        filepath = uploads_dir / filename

        with open(filepath, "wb") as f:
            f.write(imagen.file.read())

        imagen_url = f"/static/uploads/mesas/{filename}"

    mesa = Mesa(
        nombre=nombre,
        tarifa_por_hora=tarifa_por_hora,
        estado="libre",
        imagen=imagen_url
    )

    db.add(mesa)
    db.commit()
    db.refresh(mesa)
    return mesa



@router.get("/", response_model=list[MesaOut])
def listar_mesas(db: Session = Depends(get_db)):
    mesas = db.query(Mesa).all()
    resultado = []

    for mesa in mesas:
        turno_activo = db.query(Turno).filter(
            Turno.mesa_id == mesa.id,
            Turno.estado.in_(["abierto", "pausado"])
        ).order_by(Turno.id.desc()).first()

        resultado.append({
            "id": mesa.id,
            "nombre": mesa.nombre,
            "estado": mesa.estado,
            "tarifa_por_hora": mesa.tarifa_por_hora,

            "hora_inicio": turno_activo.hora_inicio if turno_activo else None,
            "turno_activo": turno_activo.id if turno_activo else None,
            "turno_estado": turno_activo.estado if turno_activo else None,

            # ✅ CLAVE para que el timer NO corra al recargar
            "pausa_inicio": turno_activo.pausa_inicio if turno_activo else None,
            "pausa_acumulada_seg": int(turno_activo.pausa_acumulada_seg or 0) if turno_activo else 0,

            "imagen": mesa.imagen,
        })

    return resultado


@router.put("/{mesa_id}", response_model=MesaOut)
def actualizar_mesa(mesa_id: int, data: MesaUpdate, db: Session = Depends(get_db)):
    mesa = db.query(Mesa).filter(Mesa.id == mesa_id).first()
    if not mesa:
        raise HTTPException(status_code=404, detail="Mesa no encontrada")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(mesa, field, value)

    db.commit()
    db.refresh(mesa)
    return mesa


@router.delete("/{mesa_id}")
def eliminar_mesa(mesa_id: int, db: Session = Depends(get_db)):
    mesa = db.query(Mesa).filter(Mesa.id == mesa_id).first()
    if not mesa:
        raise HTTPException(status_code=404, detail="Mesa no encontrada")

    db.delete(mesa)
    db.commit()
    return {"mensaje": "Mesa eliminada"}
