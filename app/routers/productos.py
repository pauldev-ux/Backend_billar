from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session, joinedload
from pathlib import Path
from uuid import uuid4

from app.database import get_db
from app.models.producto import Producto
from app.models.categoria import Categoria
from app.schemas.producto_schema import (
    ProductoCreate, ProductoUpdate, ProductoOut, ProductoStockDelta
)

router = APIRouter(prefix="/productos", tags=["Productos"])


@router.post("/", response_model=ProductoOut)
def crear_producto(data: ProductoCreate, db: Session = Depends(get_db)):
    if data.categoria_id is not None:
        cat = db.query(Categoria).filter(Categoria.id == data.categoria_id).first()
        if not cat:
            raise HTTPException(status_code=404, detail="Categoría no encontrada")

    producto = Producto(**data.model_dump())
    db.add(producto)
    db.commit()
    db.refresh(producto)
    return producto


@router.post("/con-imagen", response_model=ProductoOut)
def crear_producto_con_imagen(
    nombre: str = Form(...),
    precio_compra: float = Form(...),
    precio_venta: float = Form(...),
    cantidad: int = Form(...),
    categoria_id: int | None = Form(None),
    imagen: UploadFile | None = File(None),
    db: Session = Depends(get_db),
):
    imagen_url = None

    if imagen:
        uploads_dir = Path(__file__).resolve().parents[1] / "static" / "uploads" / "productos"
        uploads_dir.mkdir(parents=True, exist_ok=True)

        ext = Path(imagen.filename).suffix.lower()
        if ext not in [".jpg", ".jpeg", ".png", ".webp"]:
            raise HTTPException(status_code=400, detail="Formato de imagen no permitido")

        filename = f"{uuid4().hex}{ext}"
        filepath = uploads_dir / filename

        with open(filepath, "wb") as f:
            f.write(imagen.file.read())

        imagen_url = f"/static/uploads/productos/{filename}"

    if categoria_id is not None:
        cat = db.query(Categoria).filter(Categoria.id == categoria_id).first()
        if not cat:
            raise HTTPException(status_code=404, detail="Categoría no encontrada")

    producto = Producto(
        nombre=nombre,
        precio_compra=precio_compra,
        precio_venta=precio_venta,
        cantidad=cantidad,
        imagen=imagen_url,
        categoria_id=categoria_id
    )

    db.add(producto)
    db.commit()
    db.refresh(producto)
    return producto


@router.get("/", response_model=list[ProductoOut])
def listar_productos(db: Session = Depends(get_db)):
    return db.query(Producto).options(joinedload(Producto.categoria)).all()


@router.get("/{producto_id}", response_model=ProductoOut)
def obtener_producto(producto_id: int, db: Session = Depends(get_db)):
    producto = (
        db.query(Producto)
        .options(joinedload(Producto.categoria))
        .filter(Producto.id == producto_id)
        .first()
    )
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return producto


@router.put("/{producto_id}", response_model=ProductoOut)
def actualizar_producto(producto_id: int, data: ProductoUpdate, db: Session = Depends(get_db)):
    producto = db.query(Producto).filter(Producto.id == producto_id).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    data_dict = data.model_dump(exclude_unset=True)

    # ✅ validar categoria_id si viene (y no es null)
    if "categoria_id" in data_dict and data_dict["categoria_id"] is not None:
        cat = db.query(Categoria).filter(Categoria.id == data_dict["categoria_id"]).first()
        if not cat:
            raise HTTPException(status_code=404, detail="Categoría no encontrada")

    for field, value in data_dict.items():
        setattr(producto, field, value)

    db.commit()
    db.refresh(producto)
    return producto


@router.post("/{producto_id}/imagen", response_model=ProductoOut)
def actualizar_imagen_producto(
    producto_id: int,
    imagen: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    producto = db.query(Producto).filter(Producto.id == producto_id).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    uploads_dir = Path(__file__).resolve().parents[1] / "static" / "uploads" / "productos"
    uploads_dir.mkdir(parents=True, exist_ok=True)

    ext = Path(imagen.filename).suffix.lower()
    if ext not in [".jpg", ".jpeg", ".png", ".webp"]:
        raise HTTPException(status_code=400, detail="Formato de imagen no permitido")

    filename = f"{uuid4().hex}{ext}"
    filepath = uploads_dir / filename

    with open(filepath, "wb") as f:
        f.write(imagen.file.read())

    producto.imagen = f"/static/uploads/productos/{filename}"
    db.commit()
    db.refresh(producto)
    return producto


@router.patch("/{producto_id}/stock", response_model=ProductoOut)
def ajustar_stock(producto_id: int, data: ProductoStockDelta, db: Session = Depends(get_db)):
    producto = db.query(Producto).filter(Producto.id == producto_id).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    nueva_cantidad = (producto.cantidad or 0) + data.delta
    if nueva_cantidad < 0:
        raise HTTPException(status_code=400, detail="Stock insuficiente")

    producto.cantidad = nueva_cantidad
    db.commit()
    db.refresh(producto)
    return producto


@router.delete("/{producto_id}")
def eliminar_producto(producto_id: int, db: Session = Depends(get_db)):
    producto = db.query(Producto).filter(Producto.id == producto_id).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    db.delete(producto)
    db.commit()
    return {"mensaje": "Producto eliminado"}
