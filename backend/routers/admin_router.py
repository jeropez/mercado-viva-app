from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db
from auth import requerir_admin

router = APIRouter(prefix="/api/admin", tags=["administrador"])


def resolver_sede_objetivo(
    sede_id: Optional[int] = Query(
        None,
        description="Solo la usa el superadmin, para indicar qué sede quiere gestionar en este momento",
    ),
    db: Session = Depends(get_db),
    admin: models.Usuario = Depends(requerir_admin),
) -> int:
    """
    Determina sobre qué sede va a operar esta petición.

    - Un admin normal SIEMPRE opera sobre su propia sede (admin.sede_id),
      sin importar qué sede_id venga en la URL — así evitamos que alguien
      manipule la petición para tocar otra sede.
    - Un superadmin no tiene sede fija: debe indicar explícitamente
      ?sede_id=X en cada petición (el frontend lo hace automáticamente
      según la sede que haya elegido en el selector del panel).
    """
    if admin.tipo == "superadmin":
        if sede_id is None:
            raise HTTPException(
                status_code=400,
                detail="Como superadmin, debes indicar qué sede quieres gestionar",
            )
        sede = db.query(models.Sede).filter(models.Sede.id == sede_id).first()
        if sede is None:
            raise HTTPException(status_code=404, detail="La sede indicada no existe")
        return sede_id

    return admin.sede_id


def _producto_de_mi_sede_o_404(db: Session, producto_id: int, sede_objetivo: int) -> models.Producto:
    producto = db.query(models.Producto).filter(models.Producto.id == producto_id).first()
    if producto is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    if producto.sede_id != sede_objetivo:
        raise HTTPException(
            status_code=403,
            detail="Ese producto no pertenece a la sede que estás gestionando",
        )
    return producto


@router.get("/inventario", response_model=List[schemas.ProductoOut])
def listar_inventario(
    db: Session = Depends(get_db),
    sede_objetivo: int = Depends(resolver_sede_objetivo),
):
    """HU-10: consulta del inventario completo de la sede objetivo."""
    return (
        db.query(models.Producto)
        .filter(models.Producto.sede_id == sede_objetivo)
        .order_by(models.Producto.nombre)
        .all()
    )


@router.post("/productos", response_model=schemas.ProductoOut, status_code=201)
def crear_producto(
    datos: schemas.ProductoCreateRequest,
    db: Session = Depends(get_db),
    sede_objetivo: int = Depends(resolver_sede_objetivo),
):
    """HU-7: agregar un producto nuevo al catálogo de la sede objetivo."""
    duplicado = db.query(models.Producto).filter(
        models.Producto.sede_id == sede_objetivo,
        models.Producto.sku == datos.sku,
    ).first()
    if duplicado:
        raise HTTPException(status_code=409, detail="Ya existe un producto con ese SKU en esa sede")

    producto = models.Producto(sede_id=sede_objetivo, **datos.model_dump())
    db.add(producto)
    db.commit()
    db.refresh(producto)
    return producto


@router.put("/productos/{producto_id}", response_model=schemas.ProductoOut)
def actualizar_producto(
    producto_id: int,
    datos: schemas.ProductoUpdateRequest,
    db: Session = Depends(get_db),
    sede_objetivo: int = Depends(resolver_sede_objetivo),
):
    """HU-9: actualizar cantidad u otros datos de un producto existente."""
    producto = _producto_de_mi_sede_o_404(db, producto_id, sede_objetivo)

    cambios = datos.model_dump(exclude_unset=True)
    for campo, valor in cambios.items():
        setattr(producto, campo, valor)

    db.commit()
    db.refresh(producto)
    return producto


@router.delete("/productos/{producto_id}", status_code=200)
def eliminar_producto(
    producto_id: int,
    db: Session = Depends(get_db),
    sede_objetivo: int = Depends(resolver_sede_objetivo),
):
    """HU-8: eliminar (soft delete) un producto del catálogo de la sede objetivo."""
    producto = _producto_de_mi_sede_o_404(db, producto_id, sede_objetivo)
    producto.activo = False
    db.commit()
    return {"mensaje": f"Producto '{producto.nombre}' eliminado del catálogo"}


@router.get("/perfil", response_model=schemas.UsuarioOut)
def perfil_admin(admin: models.Usuario = Depends(requerir_admin)):
    return admin