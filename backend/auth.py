"""
Autenticación: hashing de contraseñas con bcrypt y tokens JWT.

JWT_SECRET debe definirse como variable de entorno en producción (Render).
En local, si no está definida, se usa una clave de desarrollo (NO usar en
producción real).
"""
import os
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from database import get_db
import models

JWT_SECRET = os.getenv("JWT_SECRET", "clave-de-desarrollo-cambiar-en-produccion")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 12

bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    # bcrypt solo admite hasta 72 bytes; se corta de forma segura si el
    # usuario ingresa una contraseña más larga.
    password_bytes = password.encode("utf-8")[:72]
    return bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    password_bytes = password.encode("utf-8")[:72]
    return bcrypt.checkpw(password_bytes, password_hash.encode("utf-8"))


def crear_token(usuario_id: int, tipo: str) -> str:
    payload = {
        "sub": str(usuario_id),
        "tipo": tipo,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRE_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def _decodificar_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="La sesión expiró, inicia sesión de nuevo")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")


def obtener_usuario_actual(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> models.Usuario:
    if credentials is None:
        raise HTTPException(status_code=401, detail="No se encontró una sesión activa")

    payload = _decodificar_token(credentials.credentials)
    usuario = db.query(models.Usuario).filter(models.Usuario.id == int(payload["sub"])).first()
    if usuario is None:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    return usuario


def requerir_cliente(usuario: models.Usuario = Depends(obtener_usuario_actual)) -> models.Usuario:
    if usuario.tipo != "cliente":
        raise HTTPException(status_code=403, detail="Esta acción es exclusiva de clientes")
    return usuario


def requerir_admin(usuario: models.Usuario = Depends(obtener_usuario_actual)) -> models.Usuario:
    """Admin normal o superadmin (ambos entran al panel de administración)."""
    if usuario.tipo not in ("admin", "superadmin"):
        raise HTTPException(status_code=403, detail="Esta acción es exclusiva de administradores")
    return usuario


def requerir_superadmin(usuario: models.Usuario = Depends(obtener_usuario_actual)) -> models.Usuario:
    if usuario.tipo != "superadmin":
        raise HTTPException(status_code=403, detail="Esta acción es exclusiva del superadministrador")
    return usuario