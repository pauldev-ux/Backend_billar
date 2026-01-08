from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.categoria import Categoria
from app.schemas.categoria_schema import CategoriaCreate, CategoriaUpdate, CategoriaOut

router = APIRouter(prefix="/categorias", tags=["Categorias"])

@router.post("/", response_model=CategoriaOut)
def crear_categoria(data: CategoriaCreate, db: Session = Depends(get_db)):
    nombre = data.nombre.strip()

    exists = db.query(Categoria).filter(Categoria.nombre == nombre).first()
    if exists:
        raise HTTPException(status_code=409, detail="Esa categoría ya existe")

    cat = Categoria(nombre=nombre)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat

@router.get("/", response_model=list[CategoriaOut])
def listar_categorias(db: Session = Depends(get_db)):
    return db.query(Categoria).order_by(Categoria.nombre.asc()).all()

@router.put("/{categoria_id}", response_model=CategoriaOut)
def actualizar_categoria(categoria_id: int, data: CategoriaUpdate, db: Session = Depends(get_db)):
    cat = db.query(Categoria).filter(Categoria.id == categoria_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")

    if data.nombre is not None:
        nombre = data.nombre.strip()
        if nombre == "":
            raise HTTPException(status_code=400, detail="El nombre no puede estar vacío")

        exists = db.query(Categoria).filter(Categoria.nombre == nombre, Categoria.id != categoria_id).first()
        if exists:
            raise HTTPException(status_code=409, detail="Esa categoría ya existe")

        cat.nombre = nombre

    db.commit()
    db.refresh(cat)
    return cat

@router.delete("/{categoria_id}")
def eliminar_categoria(categoria_id: int, db: Session = Depends(get_db)):
    cat = db.query(Categoria).filter(Categoria.id == categoria_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")

    db.delete(cat)
    db.commit()
    return {"mensaje": "Categoría eliminada"}
