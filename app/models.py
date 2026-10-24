import enum
from datetime import datetime, timedelta, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def ahora() -> datetime:
    return datetime.now(timezone.utc)


class Rol(str, enum.Enum):
    usuario = "usuario"
    tecnico = "tecnico"
    admin = "admin"


class Estado(str, enum.Enum):
    abierto = "abierto"
    en_progreso = "en_progreso"
    resuelto = "resuelto"
    cerrado = "cerrado"


class Prioridad(str, enum.Enum):
    baja = "baja"
    media = "media"
    alta = "alta"
    critica = "critica"


class Categoria(str, enum.Enum):
    hardware = "hardware"
    software = "software"
    red = "red"
    cuentas = "cuentas"
    otro = "otro"


# Horas máximas de resolución según prioridad (SLA)
SLA_HORAS = {Prioridad.critica: 4, Prioridad.alta: 24, Prioridad.media: 72, Prioridad.baja: 120}


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    rol: Mapped[Rol] = mapped_column(Enum(Rol, name="rol"), default=Rol.usuario)
    departamento: Mapped[str | None] = mapped_column(String(120))
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora)

    tickets: Mapped[list["Ticket"]] = relationship(back_populates="solicitante", foreign_keys="Ticket.solicitante_id")


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(primary_key=True)
    titulo: Mapped[str] = mapped_column(String(200))
    descripcion: Mapped[str] = mapped_column(Text)
    categoria: Mapped[Categoria] = mapped_column(Enum(Categoria, name="categoria"), default=Categoria.otro)
    prioridad: Mapped[Prioridad] = mapped_column(Enum(Prioridad, name="prioridad"), default=Prioridad.media, index=True)
    estado: Mapped[Estado] = mapped_column(Enum(Estado, name="estado"), default=Estado.abierto, index=True)

    solicitante_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"), index=True)
    asignado_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id", ondelete="SET NULL"), index=True)

    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora)
    actualizado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora, onupdate=ahora)
    vence_en: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    resuelto_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    solicitante: Mapped[Usuario] = relationship(back_populates="tickets", foreign_keys=[solicitante_id])
    asignado: Mapped[Usuario | None] = relationship(foreign_keys=[asignado_id])
    comentarios: Mapped[list["Comentario"]] = relationship(
        back_populates="ticket", cascade="all, delete-orphan", order_by="Comentario.creado_en"
    )

    def calcular_vencimiento(self) -> None:
        base = self.creado_en or ahora()
        self.vence_en = base + timedelta(hours=SLA_HORAS[self.prioridad])


class Comentario(Base):
    __tablename__ = "comentarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id", ondelete="CASCADE"), index=True)
    autor_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"))
    contenido: Mapped[str] = mapped_column(Text)
    interno: Mapped[bool] = mapped_column(default=False)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora)

    ticket: Mapped[Ticket] = relationship(back_populates="comentarios")
    autor: Mapped[Usuario] = relationship()
