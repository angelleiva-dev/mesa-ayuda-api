from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select

from app.deps import DB, Actual
from app.models import Usuario
from app.schemas import Token, UsuarioCrear, UsuarioPublico
from app.security import crear_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post("/registro", response_model=UsuarioPublico, status_code=status.HTTP_201_CREATED)
def registro(datos: UsuarioCrear, db: DB):
    """Crea una cuenta con rol `usuario`. Los roles técnico/admin los asigna un administrador."""
    if db.scalar(select(Usuario).where(Usuario.email == datos.email.lower())):
        raise HTTPException(status.HTTP_409_CONFLICT, "El email ya está registrado")
    usuario = Usuario(
        nombre=datos.nombre,
        email=datos.email.lower(),
        password_hash=hash_password(datos.password),
        departamento=datos.departamento,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


@router.post("/login", response_model=Token)
def login(form: Annotated[OAuth2PasswordRequestForm, Depends()], db: DB):
    """Inicia sesión con email (campo `username`) y contraseña. Devuelve un JWT."""
    usuario = db.scalar(select(Usuario).where(Usuario.email == form.username.lower()))
    if not usuario or not verify_password(form.password, usuario.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Email o contraseña incorrectos")
    return Token(access_token=crear_token(str(usuario.id)))


@router.get("/me", response_model=UsuarioPublico)
def perfil(usuario: Actual):
    return usuario
