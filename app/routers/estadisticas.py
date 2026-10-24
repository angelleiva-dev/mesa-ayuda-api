from fastapi import APIRouter
from sqlalchemy import func, select

from app.deps import DB, Staff
from app.models import Categoria, Estado, Prioridad, Ticket, ahora
from app.routers.tickets import ABIERTOS, utc
from app.schemas import Resumen

router = APIRouter(prefix="/estadisticas", tags=["Estadísticas"])


def conteo(db, columna, enum_cls) -> dict[str, int]:
    filas = dict(db.execute(select(columna, func.count()).group_by(columna)).all())
    return {e.value: filas.get(e, 0) for e in enum_cls}


@router.get("/resumen", response_model=Resumen)
def resumen(db: DB, _: Staff):
    """Indicadores para el panel del equipo técnico."""
    abiertos = db.scalars(select(Ticket.vence_en).where(Ticket.estado.in_(ABIERTOS))).all()
    resueltos = db.execute(
        select(Ticket.creado_en, Ticket.resuelto_en).where(Ticket.resuelto_en.is_not(None))
    ).all()
    horas = [(utc(fin) - utc(ini)).total_seconds() / 3600 for ini, fin in resueltos]
    return Resumen(
        total=db.scalar(select(func.count(Ticket.id))),
        por_estado=conteo(db, Ticket.estado, Estado),
        por_prioridad=conteo(db, Ticket.prioridad, Prioridad),
        por_categoria=conteo(db, Ticket.categoria, Categoria),
        vencidos=sum(1 for v in abiertos if utc(v) < ahora()),
        horas_promedio_resolucion=round(sum(horas) / len(horas), 1) if horas else None,
    )
