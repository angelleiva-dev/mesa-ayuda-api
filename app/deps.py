from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Rol, Usuario
from app.security import leer_token

oauth2 = OAuth2PasswordBearer(tokenUrl="/auth/login")

DB = Annotated[Session, Depends(get_db)]


def usuario_actual(db: DB, token: Annotated[str, Depends(oauth2)]) -> Usuario:
    credenciales_invalidas = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales inválidas o expiradas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    sub = leer_token(token)
    if sub is None:
        raise credenciales_invalidas
    usuario = db.get(Usuario, int(sub))
    if usuario is None:
        raise credenciales_invalidas
    return usuario


Actual = Annotated[Usuario, Depends(usuario_actual)]


def requiere_rol(*roles: Rol):
    def verificar(usuario: Actual) -> Usuario:
        if usuario.rol not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "No tienes permisos para esta acción")
        return usuario

    return verificar


Staff = Annotated[Usuario, Depends(requiere_rol(Rol.tecnico, Rol.admin))]
Admin = Annotated[Usuario, Depends(requiere_rol(Rol.admin))]
