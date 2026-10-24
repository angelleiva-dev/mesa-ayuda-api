import os
import tempfile

# La base de pruebas es un SQLite temporal: los tests no necesitan PostgreSQL
os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.gettempdir()}/mesa_ayuda_test.db"

import pytest
from fastapi.testclient import TestClient

from app.database import Base, SessionLocal, engine
from app.main import app
from app.models import Rol, Usuario
from app.security import hash_password


@pytest.fixture(autouse=True)
def base_limpia():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def crear_usuario(email: str, rol: Rol = Rol.usuario) -> None:
    with SessionLocal() as db:
        db.add(Usuario(nombre=email.split("@")[0].title(), email=email, rol=rol, password_hash=hash_password("password123")))
        db.commit()


def auth(client: TestClient, email: str) -> dict[str, str]:
    r = client.post("/auth/login", data={"username": email, "password": "password123"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def usuario(client):
    crear_usuario("ana@mesa.cl")
    return auth(client, "ana@mesa.cl")


@pytest.fixture
def otro_usuario(client):
    crear_usuario("luis@mesa.cl")
    return auth(client, "luis@mesa.cl")


@pytest.fixture
def tecnico(client):
    crear_usuario("tec@mesa.cl", Rol.tecnico)
    return auth(client, "tec@mesa.cl")


@pytest.fixture
def admin(client):
    crear_usuario("admin@mesa.cl", Rol.admin)
    return auth(client, "admin@mesa.cl")
