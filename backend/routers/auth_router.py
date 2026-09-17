from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db
from auth import hash_password, verify_password, crear_token

router = APIRouter(prefix="/api/auth", tags=["autenticación"])


@router.post("/registro/cliente", response_model=schemas.TokenResponse, status_code=201)
def registro_cliente(datos: schemas.RegistroClienteRequest, db: Session = Depends(get_db)):
    existe = db.query(models.Usuario).filter(
        (models.Usuario.email == datos.email) | (models.Usuario.documento == datos.documento)
    ).first()
    if existe:
        raise HTTPException(status_code=409, detail="Ya existe una cuenta con ese correo o documento")

    usuario = models.Usuario(
        tipo="cliente",
        nombres=datos.nombres,
        apellidos=datos.apellidos,
        email=datos.email,
        documento=datos.documento,
        telefono=datos.telefono,
        direccion=datos.direccion,
        ciudad=datos.ciudad,
        password_hash=hash_password(datos.password),
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)

    token = crear_token(usuario.id, usuario.tipo)
    return schemas.TokenResponse(access_token=token, usuario=usuario)


@router.post("/registro/admin", response_model=schemas.TokenResponse, status_code=201)
def registro_admin(datos: schemas.RegistroAdminRequest, db: Session = Depends(get_db)):
    existe = db.query(models.Usuario).filter(
        (models.Usuario.email == datos.email) | (models.Usuario.documento == datos.documento)
    ).first()
    if existe:
        raise HTTPException(status_code=409, detail="Ya existe una cuenta con ese correo o documento")

    # --- Lista blanca: el correo debe haber sido autorizado manualmente
    #     en la base de datos (ver backend/gestionar_admins.py) ---
    autorizado = db.query(models.CorreoAutorizado).filter(
        models.CorreoAutorizado.email == datos.email
    ).first()
    if autorizado is None:
        raise HTTPException(
            status_code=403,
            detail="Este correo no está autorizado para crear una cuenta de administrador. "
                   "Contacta al equipo de Mercado VIVA para que lo agreguen a la lista autorizada.",
        )

    # La sede (o la ausencia de sede fija, si es superadmin) viene de la
    # lista blanca, nunca de lo que el formulario envíe.
    if autorizado.rol == "admin" and autorizado.sede_id is None:
        raise HTTPException(
            status_code=500,
            detail="Este correo está autorizado como admin pero no tiene una sede asignada. "
                   "Contacta al equipo técnico.",
        )

    usuario = models.Usuario(
        tipo=autorizado.rol,  # "admin" o "superadmin"
        nombres=datos.nombres,
        apellidos=datos.apellidos,
        email=datos.email,
        documento=datos.documento,
        telefono=datos.telefono,
        sede_id=autorizado.sede_id,  # None si es superadmin
        password_hash=hash_password(datos.password),
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)

    token = crear_token(usuario.id, usuario.tipo)
    return schemas.TokenResponse(access_token=token, usuario=usuario)


@router.post("/login", response_model=schemas.TokenResponse)
def login(datos: schemas.LoginRequest, db: Session = Depends(get_db)):
    usuario = db.query(models.Usuario).filter(models.Usuario.email == datos.email).first()

    # Mensaje genérico a propósito: no revelar si falló el correo o la contraseña.
    if usuario is None or not verify_password(datos.password, usuario.password_hash):
        raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos")

    token = crear_token(usuario.id, usuario.tipo)
    return schemas.TokenResponse(access_token=token, usuario=usuario)


@router.get("/sedes", response_model=list[schemas.SedeOut])
def listar_sedes_publico(db: Session = Depends(get_db)):
    """Público: se usa en los formularios de registro/selección de sede."""
    return db.query(models.Sede).order_by(models.Sede.nombre).all()
