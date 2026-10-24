def test_registro_y_login(client):
    r = client.post("/auth/registro", json={"nombre": "Ana Pérez", "email": "Ana@Mesa.cl", "password": "segura123"})
    assert r.status_code == 201
    assert r.json()["rol"] == "usuario"
    assert r.json()["email"] == "ana@mesa.cl"

    r = client.post("/auth/login", data={"username": "ana@mesa.cl", "password": "segura123"})
    assert r.status_code == 200
    token = r.json()["access_token"]

    r = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.json()["nombre"] == "Ana Pérez"


def test_email_duplicado(client):
    datos = {"nombre": "Ana", "email": "ana@mesa.cl", "password": "segura123"}
    client.post("/auth/registro", json=datos)
    assert client.post("/auth/registro", json=datos).status_code == 409


def test_password_incorrecta(client):
    client.post("/auth/registro", json={"nombre": "Ana", "email": "ana@mesa.cl", "password": "segura123"})
    r = client.post("/auth/login", data={"username": "ana@mesa.cl", "password": "otra-clave"})
    assert r.status_code == 401


def test_validacion_password_corta(client):
    r = client.post("/auth/registro", json={"nombre": "Ana", "email": "ana@mesa.cl", "password": "123"})
    assert r.status_code == 422


def test_ruta_protegida_sin_token(client):
    assert client.get("/tickets").status_code == 401
    assert client.get("/tickets", headers={"Authorization": "Bearer token-falso"}).status_code == 401
