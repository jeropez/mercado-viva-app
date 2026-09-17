"""
Gestión de la lista blanca de correos autorizados a crear cuentas de
administrador o superadmin en Mercado VIVA.

Este script es la forma "manual" de autorizar a alguien: solo el equipo
que tiene acceso a la base de datos (local o de Render) puede correrlo.
Nadie puede autorizarse a sí mismo desde la página web.

USO (desde la carpeta backend/):

  Autorizar un admin de una sede específica:
    python gestionar_admins.py agregar admin correo@mercadoviva.com --sede 1

  Autorizar un superadmin (sin sede fija, la elige él mismo al entrar):
    python gestionar_admins.py agregar superadmin correo@mercadoviva.com

  Ver la lista completa de correos autorizados:
    python gestionar_admins.py listar

  Quitar la autorización de un correo:
    python gestionar_admins.py quitar correo@mercadoviva.com

Para usarlo contra la base de datos de Render (no la local), define la
variable de entorno DATABASE_URL antes de correr el script, por ejemplo:

  set DATABASE_URL=postgresql://usuario:clave@host/mercado_viva   (Windows)
  export DATABASE_URL=postgresql://usuario:clave@host/mercado_viva (Mac/Linux)

La cadena de conexión la encuentras en Render → tu base de datos →
"External Database URL".
"""
import argparse
import sys

from database import SessionLocal, Base, engine
import models


def agregar(email: str, rol: str, sede_id: int | None, notas: str | None):
    if rol not in ("admin", "superadmin"):
        print("Error: el rol debe ser 'admin' o 'superadmin'")
        sys.exit(1)
    if rol == "admin" and sede_id is None:
        print("Error: un correo con rol 'admin' necesita --sede <id>")
        sys.exit(1)

    db = SessionLocal()
    try:
        if sede_id is not None:
            sede = db.query(models.Sede).filter(models.Sede.id == sede_id).first()
            if sede is None:
                print(f"Error: no existe ninguna sede con id={sede_id}")
                print("Sedes disponibles:")
                for s in db.query(models.Sede).all():
                    print(f"  {s.id} -> {s.nombre}")
                sys.exit(1)

        existente = db.query(models.CorreoAutorizado).filter(
            models.CorreoAutorizado.email == email
        ).first()
        if existente:
            existente.rol = rol
            existente.sede_id = sede_id if rol == "admin" else None
            existente.notas = notas
            db.commit()
            print(f"Actualizado: {email} -> rol={rol}, sede_id={existente.sede_id}")
        else:
            nuevo = models.CorreoAutorizado(
                email=email,
                rol=rol,
                sede_id=sede_id if rol == "admin" else None,
                notas=notas,
            )
            db.add(nuevo)
            db.commit()
            print(f"Agregado: {email} -> rol={rol}, sede_id={nuevo.sede_id}")
    finally:
        db.close()


def listar():
    db = SessionLocal()
    try:
        correos = db.query(models.CorreoAutorizado).order_by(models.CorreoAutorizado.email).all()
        if not correos:
            print("No hay correos autorizados todavía.")
            return
        print(f"{'EMAIL':<35} {'ROL':<12} {'SEDE':<20} NOTAS")
        print("-" * 85)
        for c in correos:
            sede_nombre = c.sede.nombre if c.sede else "(elige al entrar)"
            print(f"{c.email:<35} {c.rol:<12} {sede_nombre:<20} {c.notas or ''}")
    finally:
        db.close()


def quitar(email: str):
    db = SessionLocal()
    try:
        correo = db.query(models.CorreoAutorizado).filter(
            models.CorreoAutorizado.email == email
        ).first()
        if correo is None:
            print(f"No se encontró ningún correo autorizado con: {email}")
            sys.exit(1)
        db.delete(correo)
        db.commit()
        print(f"Se quitó la autorización de: {email}")
        print("(La cuenta de usuario, si ya se había registrado, NO se elimina con esto.)")
    finally:
        db.close()


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)  # por si se corre antes que la app

    parser = argparse.ArgumentParser(description="Gestión de correos autorizados como admin/superadmin")
    sub = parser.add_subparsers(dest="comando", required=True)

    p_agregar = sub.add_parser("agregar", help="Autorizar un correo nuevo")
    p_agregar.add_argument("rol", choices=["admin", "superadmin"])
    p_agregar.add_argument("email")
    p_agregar.add_argument("--sede", type=int, default=None, help="ID de la sede (requerido si rol=admin)")
    p_agregar.add_argument("--notas", default=None)

    sub.add_parser("listar", help="Ver todos los correos autorizados")

    p_quitar = sub.add_parser("quitar", help="Quitar la autorización de un correo")
    p_quitar.add_argument("email")

    args = parser.parse_args()

    if args.comando == "agregar":
        agregar(args.email, args.rol, args.sede, args.notas)
    elif args.comando == "listar":
        listar()
    elif args.comando == "quitar":
        quitar(args.email)