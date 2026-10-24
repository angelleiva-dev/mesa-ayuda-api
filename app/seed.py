"""Carga datos de ejemplo:  python -m app.seed"""
from datetime import timedelta

from app.database import Base, SessionLocal, engine
from app.models import Categoria, Comentario, Estado, Prioridad, Rol, Ticket, Usuario, ahora
from app.security import hash_password

USUARIOS = [
    ("Administrador", "admin@mesa.cl", Rol.admin, "Informática"),
    ("Camila Muñoz", "tecnico@mesa.cl", Rol.tecnico, "Informática"),
    ("Jorge Rojas", "usuario@mesa.cl", Rol.usuario, "Finanzas"),
]

TICKETS = [
    ("Impresora del segundo piso no imprime", "La impresora muestra error de papel atascado pero no hay papel.", Categoria.hardware, Prioridad.media, Estado.abierto, 2),
    ("No puedo acceder al sistema de remuneraciones", "Al iniciar sesión aparece 'usuario bloqueado'.", Categoria.cuentas, Prioridad.alta, Estado.en_progreso, 6),
    ("Sin conexión a internet en oficina de partes", "Desde esta mañana ningún equipo de la oficina tiene red.", Categoria.red, Prioridad.critica, Estado.resuelto, 30),
    ("Instalar software de firma electrónica", "Necesito instalar el software para firmar decretos.", Categoria.software, Prioridad.baja, Estado.abierto, 1),
]


def run() -> None:
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        if db.query(Usuario).count():
            print("La base ya tiene datos, no se cargó nada.")
            return
        users = [Usuario(nombre=n, email=e, rol=r, departamento=d, password_hash=hash_password("password123")) for n, e, r, d in USUARIOS]
        db.add_all(users)
        db.flush()
        admin, tecnico, usuario = users
        for titulo, desc, cat, prio, estado, horas in TICKETS:
            t = Ticket(titulo=titulo, descripcion=desc, categoria=cat, prioridad=prio, estado=estado,
                       solicitante_id=usuario.id, creado_en=ahora() - timedelta(hours=horas))
            t.calcular_vencimiento()
            if estado != Estado.abierto:
                t.asignado_id = tecnico.id
            if estado == Estado.resuelto:
                t.resuelto_en = t.creado_en + timedelta(hours=3)
            db.add(t)
            db.flush()
            if estado == Estado.resuelto:
                db.add(Comentario(ticket_id=t.id, autor_id=tecnico.id, contenido="Se reinició el switch del rack. Conexión restablecida."))
        db.commit()
        print("Datos de ejemplo cargados. Contraseña para todos: password123")


if __name__ == "__main__":
    run()
