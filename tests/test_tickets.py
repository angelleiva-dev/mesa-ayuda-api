TICKET = {"titulo": "Impresora no funciona", "descripcion": "La impresora del segundo piso no imprime.", "categoria": "hardware", "prioridad": "alta"}


def crear_ticket(client, headers, **extra):
    r = client.post("/tickets", json={**TICKET, **extra}, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()


def test_crear_ticket_calcula_sla(client, usuario):
    t = crear_ticket(client, usuario)
    assert t["estado"] == "abierto"
    assert t["vencido"] is False
    assert t["solicitante"]["nombre"] == "Ana"


def test_usuario_solo_ve_sus_tickets(client, usuario, otro_usuario, tecnico):
    crear_ticket(client, usuario)
    t2 = crear_ticket(client, otro_usuario)

    assert client.get("/tickets", headers=usuario).json()["total"] == 1
    assert client.get(f"/tickets/{t2['id']}", headers=usuario).status_code == 404
    assert client.get("/tickets", headers=tecnico).json()["total"] == 2


def test_filtros_y_busqueda(client, usuario, tecnico):
    crear_ticket(client, usuario)
    crear_ticket(client, usuario, titulo="Sin acceso a la red", descripcion="Ningún equipo de la oficina tiene conexión.", categoria="red", prioridad="critica")

    assert client.get("/tickets?categoria=red", headers=tecnico).json()["total"] == 1
    assert client.get("/tickets?prioridad=alta", headers=tecnico).json()["total"] == 1
    assert client.get("/tickets?q=impresora", headers=tecnico).json()["total"] == 1
    pagina = client.get("/tickets?por_pagina=1&pagina=2", headers=tecnico).json()
    assert pagina["total"] == 2 and len(pagina["items"]) == 1


def test_asignar_pasa_a_en_progreso_y_resolver(client, usuario, tecnico):
    t = crear_ticket(client, usuario)
    tec_id = client.get("/auth/me", headers=tecnico).json()["id"]

    r = client.patch(f"/tickets/{t['id']}", json={"asignado_id": tec_id}, headers=tecnico)
    assert r.json()["estado"] == "en_progreso"
    assert r.json()["asignado"]["id"] == tec_id

    r = client.patch(f"/tickets/{t['id']}", json={"estado": "resuelto"}, headers=tecnico)
    assert r.json()["resuelto_en"] is not None


def test_no_se_puede_asignar_a_usuario_normal(client, usuario, otro_usuario, tecnico):
    t = crear_ticket(client, usuario)
    otro_id = client.get("/auth/me", headers=otro_usuario).json()["id"]
    r = client.patch(f"/tickets/{t['id']}", json={"asignado_id": otro_id}, headers=tecnico)
    assert r.status_code == 400


def test_usuario_no_puede_cambiar_estado_ni_prioridad(client, usuario):
    t = crear_ticket(client, usuario)
    assert client.patch(f"/tickets/{t['id']}", json={"estado": "cerrado"}, headers=usuario).status_code == 403
    r = client.patch(f"/tickets/{t['id']}", json={"titulo": "Impresora atascada"}, headers=usuario)
    assert r.status_code == 200 and r.json()["titulo"] == "Impresora atascada"


def test_comentarios_e_internos(client, usuario, tecnico):
    t = crear_ticket(client, usuario)
    client.post(f"/tickets/{t['id']}/comentarios", json={"contenido": "Voy en camino"}, headers=tecnico)
    client.post(f"/tickets/{t['id']}/comentarios", json={"contenido": "Revisar tóner", "interno": True}, headers=tecnico)

    assert len(client.get(f"/tickets/{t['id']}/comentarios", headers=tecnico).json()) == 2
    assert len(client.get(f"/tickets/{t['id']}/comentarios", headers=usuario).json()) == 1
    r = client.post(f"/tickets/{t['id']}/comentarios", json={"contenido": "x", "interno": True}, headers=usuario)
    assert r.status_code == 403


def test_solo_admin_elimina(client, usuario, tecnico, admin):
    t = crear_ticket(client, usuario)
    assert client.delete(f"/tickets/{t['id']}", headers=tecnico).status_code == 403
    assert client.delete(f"/tickets/{t['id']}", headers=admin).status_code == 204
    assert client.get(f"/tickets/{t['id']}", headers=admin).status_code == 404


def test_estadisticas(client, usuario, tecnico):
    t = crear_ticket(client, usuario)
    crear_ticket(client, usuario, prioridad="baja")
    client.patch(f"/tickets/{t['id']}", json={"estado": "resuelto"}, headers=tecnico)

    r = client.get("/estadisticas/resumen", headers=tecnico).json()
    assert r["total"] == 2
    assert r["por_estado"]["resuelto"] == 1
    assert r["por_prioridad"]["baja"] == 1
    assert r["horas_promedio_resolucion"] is not None
    assert client.get("/estadisticas/resumen", headers=usuario).status_code == 403
