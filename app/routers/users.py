from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.user_schema import UserCreate, UserOut, UserUpdate
from passlib.context import CryptContext
from app.deps import get_current_user

router = APIRouter(prefix="/users", tags=["Usuarios"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.post("/", response_model=UserOut)
def create_user(data: UserCreate, db: Session = Depends(get_db)):
    username = data.username.strip()

    exists = db.query(User).filter(User.username == username).first()
    if exists:
        raise HTTPException(status_code=409, detail="Ese usuario ya existe")

    hashed = pwd_context.hash(data.password)
    new_user = User(username=username, password_hash=hashed, rol=data.rol)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user



@router.get("/", response_model=list[UserOut])
def get_users(db: Session = Depends(get_db)):
    return db.query(User).all()

@router.get("/me", response_model=UserOut)
def obtener_usuario_logeado(user = Depends(get_current_user)):
    return user


@router.put("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.rol != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo admin")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if data.username is not None:
        new_username = data.username.strip()
        if new_username == "":
            raise HTTPException(status_code=400, detail="El usuario no puede estar vacío")

        exists = db.query(User).filter(User.username == new_username, User.id != user_id).first()
        if exists:
            raise HTTPException(status_code=409, detail="Ese usuario ya existe")

        user.username = new_username

    if data.password is not None:
        new_password = data.password.strip()
        if new_password == "":
            raise HTTPException(status_code=400, detail="La contraseña no puede estar vacía")
        user.password_hash = pwd_context.hash(new_password)

    db.commit()
    db.refresh(user)
    return user