from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models import Categoria, Estado, Prioridad, Rol


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---------- Usuarios ----------
class UsuarioCrear(BaseModel):
    nombre: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    departamento: str | None = None


class UsuarioPublico(ORM):
    id: int
    nombre: str
    email: EmailStr
    rol: Rol
    departamento: str | None


class CambiarRol(BaseModel):
    rol: Rol


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------- Tickets ----------
class TicketCrear(BaseModel):
    titulo: str = Field(min_length=5, max_length=200)
    descripcion: str = Field(min_length=10)
    categoria: Categoria = Categoria.otro
    prioridad: Prioridad = Prioridad.media


class TicketActualizar(BaseModel):
    titulo: str | None = Field(default=None, min_length=5, max_length=200)
    descripcion: str | None = Field(default=None, min_length=10)
    categoria: Categoria | None = None
    prioridad: Prioridad | None = None
    estado: Estado | None = None
    asignado_id: int | None = None


class UsuarioMini(ORM):
    id: int
    nombre: str


class TicketSalida(ORM):
    id: int
    titulo: str
    descripcion: str
    categoria: Categoria
    prioridad: Prioridad
    estado: Estado
    solicitante: UsuarioMini
    asignado: UsuarioMini | None
    creado_en: datetime
    actualizado_en: datetime
    vence_en: datetime
    resuelto_en: datetime | None
    vencido: bool = False


class PaginaTickets(BaseModel):
    total: int
    pagina: int
    por_pagina: int
    items: list[TicketSalida]


# ---------- Comentarios ----------
class ComentarioCrear(BaseModel):
    contenido: str = Field(min_length=1, max_length=5000)
    interno: bool = False


class ComentarioSalida(ORM):
    id: int
    contenido: str
    interno: bool
    autor: UsuarioMini
    creado_en: datetime


# ---------- Estadísticas ----------
class Resumen(BaseModel):
    total: int
    por_estado: dict[str, int]
    por_prioridad: dict[str, int]
    por_categoria: dict[str, int]
    vencidos: int
    horas_promedio_resolucion: float | None
