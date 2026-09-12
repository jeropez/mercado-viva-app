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

    sede = db.query(models.Sede).filter(models.Sede.id == datos.sede_id).first()
    if sede is None:
        raise HTTPException(status_code=404, detail="La sede seleccionada no existe")

    usuario = models.Usuario(
        tipo="admin",
        nombres=datos.nombres,
        apellidos=datos.apellidos,
        email=datos.email,
        documento=datos.documento,
        telefono=datos.telefono,
        sede_id=datos.sede_id,
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
