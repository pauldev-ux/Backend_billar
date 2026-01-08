from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm

from app.database import get_db
from app.models.user import User
from app.schemas.auth_schema import LoginSchema, TokenOut, UserAuthOut
from app.utils.security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Auth"])


# REGISTRO
@router.post("/register", response_model=UserAuthOut)
def register(data: LoginSchema, db: Session = Depends(get_db)):
    # username único
    exists = db.query(User).filter(User.username == data.username).first()
    if exists:
        raise HTTPException(400, "El usuario ya existe")

    new_user = User(
        username=data.username,
        password_hash=hash_password(data.password),
        rol="empleado"  # por defecto
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


# LOGIN - usa form-data (requerido por OAuth2PasswordBearer)
@router.post("/login", response_model=TokenOut)
def login(form: OAuth2PasswordRequestForm = Depends(),
          db: Session = Depends(get_db)):

    user = db.query(User).filter(User.username == form.username).first()

    if not user:
        raise HTTPException(401, "Usuario no encontrado")

    if not verify_password(form.password, user.password_hash):
        raise HTTPException(401, "Contraseña incorrecta")

    token = create_access_token({"sub": str(user.id)})

    return TokenOut(access_token=token)
