"""
Configuración de la base de datos.

En local, si no se define DATABASE_URL, se usa un archivo SQLite para
poder desarrollar sin instalar nada más.

En Render, se define la variable de entorno DATABASE_URL apuntando a la
base de datos PostgreSQL gestionada que provee Render. SQLAlchemy necesita
el prefijo "postgresql://" (Render a veces entrega "postgres://", por eso
se normaliza abajo).
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./mercado_viva.db")

# Render (y algunos proveedores) entregan la URL como "postgres://", pero
# SQLAlchemy 1.4+/2.x requiere "postgresql://".
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
