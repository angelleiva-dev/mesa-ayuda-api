from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query, Response, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import selectinload

from app.deps import DB, Actual, Admin
from app.models import Categoria, Comentario, Estado, Prioridad, Rol, Ticket, Usuario, ahora
from app.schemas import (
    ComentarioCrear,
    ComentarioSalida,
    PaginaTickets,
    TicketActualizar,
    TicketCrear,
    TicketSalida,
)

router = APIRouter(prefix="/tickets", tags=["Tickets"])

ABIERTOS = (Estado.abierto, Estado.en_progreso)


def utc(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def a_salida(t: Ticket) -> TicketSalida:
    salida = TicketSalida.model_validate(t)
    salida.vencido = t.estado in ABIERTOS and utc(t.vence_en) < ahora()
    return salida


def es_staff(u: Usuario) -> bool:
    return u.rol in (Rol.tecnico, Rol.admin)


def obtener_ticket(db, ticket_id: int, usuario: Usuario) -> Ticket:
    ticket = db.get(Ticket, ticket_id)
    # Un usuario normal solo ve sus propios tickets; respondemos 404 para no revelar que existe
    if not ticket or (not es_staff(usuario) and ticket.solicitante_id != usuario.id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ticket no encontrado")
    return ticket


@router.post("", response_model=TicketSalida, status_code=status.HTTP_201_CREATED)
def crear(datos: TicketCrear, db: DB, usuario: Actual):
    ticket = Ticket(**datos.model_dump(), solicitante_id=usuario.id, creado_en=ahora())
    ticket.calcular_vencimiento()
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return a_salida(ticket)


@router.get("", response_model=PaginaTickets)
def listar(
    db: DB,
    usuario: Actual,
    estado: Estado | None = None,
    prioridad: Prioridad | None = None,
    categoria: Categoria | None = None,
    asignado_a_mi: bool = False,
    q: str | None = Query(default=None, description="Busca en título y descripción"),
    pagina: int = Query(default=1, ge=1),
    por_pagina: int = Query(default=20, ge=1, le=100),
):
    filtros = []
    if not es_staff(usuario):
        filtros.append(Ticket.solicitante_id == usuario.id)
    if asignado_a_mi:
        filtros.append(Ticket.asignado_id == usuario.id)
    if estado:
        filtros.append(Ticket.estado == estado)
    if prioridad:
        filtros.append(Ticket.prioridad == prioridad)
    if categoria:
        filtros.append(Ticket.categoria == categoria)
    if q:
        patron = f"%{q.strip()}%"
        filtros.append(or_(Ticket.titulo.ilike(patron), Ticket.descripcion.ilike(patron)))

    total = db.scalar(select(func.count(Ticket.id)).where(*filtros))
    items = db.scalars(
        select(Ticket)
        .where(*filtros)
        .options(selectinload(Ticket.solicitante), selectinload(Ticket.asignado))
        .order_by(Ticket.creado_en.desc(), Ticket.id.desc())
        .offset((pagina - 1) * por_pagina)
        .limit(por_pagina)
    ).all()
    return PaginaTickets(total=total, pagina=pagina, por_pagina=por_pagina, items=[a_salida(t) for t in items])


@router.get("/{ticket_id}", response_model=TicketSalida)
def detalle(ticket_id: int, db: DB, usuario: Actual):
    return a_salida(obtener_ticket(db, ticket_id, usuario))


@router.patch("/{ticket_id}", response_model=TicketSalida)
def actualizar(ticket_id: int, datos: TicketActualizar, db: DB, usuario: Actual):
    ticket = obtener_ticket(db, ticket_id, usuario)
    cambios = datos.model_dump(exclude_unset=True)

    if not es_staff(usuario):
        # El solicitante solo puede editar texto y categoría mientras el ticket esté abierto
        no_permitidos = set(cambios) - {"titulo", "descripcion", "categoria"}
        if no_permitidos:
            raise HTTPException(status.HTTP_403_FORBIDDEN, f"No puedes modificar: {', '.join(sorted(no_permitidos))}")
        if ticket.estado != Estado.abierto:
            raise HTTPException(status.HTTP_409_CONFLICT, "Solo puedes editar tickets en estado abierto")

    if "asignado_id" in cambios and cambios["asignado_id"] is not None:
        tecnico = db.get(Usuario, cambios["asignado_id"])
        if not tecnico or not es_staff(tecnico):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Solo se puede asignar a técnicos o administradores")
        if ticket.estado == Estado.abierto and "estado" not in cambios:
            cambios["estado"] = Estado.en_progreso

    for campo, valor in cambios.items():
        setattr(ticket, campo, valor)

    if "prioridad" in cambios:
        ticket.calcular_vencimiento()
    if "estado" in cambios:
        ticket.resuelto_en = ahora() if ticket.estado in (Estado.resuelto, Estado.cerrado) else None

    db.commit()
    db.refresh(ticket)
    return a_salida(ticket)


@router.delete("/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar(ticket_id: int, db: DB, admin: Admin):
    ticket = obtener_ticket(db, ticket_id, admin)
    db.delete(ticket)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------- Comentarios ----------
@router.get("/{ticket_id}/comentarios", response_model=list[ComentarioSalida])
def listar_comentarios(ticket_id: int, db: DB, usuario: Actual):
    ticket = obtener_ticket(db, ticket_id, usuario)
    # Las notas internas solo las ve el equipo técnico
    return [c for c in ticket.comentarios if es_staff(usuario) or not c.interno]


@router.post("/{ticket_id}/comentarios", response_model=ComentarioSalida, status_code=status.HTTP_201_CREATED)
def comentar(ticket_id: int, datos: ComentarioCrear, db: DB, usuario: Actual):
    ticket = obtener_ticket(db, ticket_id, usuario)
    if datos.interno and not es_staff(usuario):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Solo el equipo técnico puede crear notas internas")
    comentario = Comentario(ticket_id=ticket.id, autor_id=usuario.id, **datos.model_dump())
    db.add(comentario)
    db.commit()
    db.refresh(comentario)
    return comentario
