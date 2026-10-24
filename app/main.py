from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import auth, estadisticas, tickets, usuarios


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Para un proyecto más grande usaría Alembic para las migraciones
    Base.metadata.create_all(engine)
    yield


app = FastAPI(
    title="Mesa de Ayuda TI · API",
    description=(
        "API REST para gestionar solicitudes de soporte técnico: tickets con prioridades y SLA, "
        "asignación a técnicos, comentarios y notas internas, y estadísticas para el equipo.\n\n"
        "**Roles:** `usuario` (crea y sigue sus tickets) · `tecnico` (atiende todos) · `admin` (gestiona usuarios)."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

app.include_router(auth.router)
app.include_router(tickets.router)
app.include_router(usuarios.router)
app.include_router(estadisticas.router)


@app.get("/", tags=["Estado"])
def raiz():
    return {"servicio": "Mesa de Ayuda TI", "version": app.version, "docs": "/docs"}
