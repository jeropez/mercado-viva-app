"""
Mercado VIVA — API principal.

Sirve la API bajo /api/* y el frontend estático (cliente y administrador)
desde la carpeta ../frontend, para poder desplegar todo como un solo
servicio en Render.
"""
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from database import Base, engine
from seed import cargar_datos_semilla
from routers import auth_router, cliente_router, admin_router

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

app = FastAPI(title="Mercado VIVA — Gestión de Inventario")

# En producción, reemplazar "*" por el dominio real del frontend desplegado.
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[ALLOWED_ORIGINS] if ALLOWED_ORIGINS != "*" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    cargar_datos_semilla()


app.include_router(auth_router.router)
app.include_router(cliente_router.router)
app.include_router(admin_router.router)


# ---------------------------------------------------------------------------
# Frontend estático
# ---------------------------------------------------------------------------

app.mount("/css", StaticFiles(directory=FRONTEND_DIR / "css"), name="css")
app.mount("/js", StaticFiles(directory=FRONTEND_DIR / "js"), name="js")
app.mount("/img", StaticFiles(directory=FRONTEND_DIR / "img"), name="img")


@app.get("/")
def servir_cliente():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/admin")
def servir_admin():
    return FileResponse(FRONTEND_DIR / "admin.html")


@app.get("/api/salud")
def salud():
    return {"estado": "ok"}
