from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.deps import DB, Admin, Staff
from app.models import Rol, Usuario
from app.schemas import CambiarRol, UsuarioPublico

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


@router.get("", response_model=list[UsuarioPublico])
def listar(db: DB, _: Staff, rol: Rol | None = None):
    consulta = select(Usuario).order_by(Usuario.nombre)
    if rol:
        consulta = consulta.where(Usuario.rol == rol)
    return db.scalars(consulta).all()


@router.patch("/{usuario_id}/rol", response_model=UsuarioPublico)
def cambiar_rol(usuario_id: int, datos: CambiarRol, db: DB, admin: Admin):
    usuario = db.get(Usuario, usuario_id)
    if not usuario:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuario no encontrado")
    if usuario.id == admin.id and datos.rol != Rol.admin:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No puedes quitarte el rol de administrador")
    usuario.rol = datos.rol
    db.commit()
    return usuario
