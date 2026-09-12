from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db
from auth import requerir_admin

router = APIRouter(prefix="/api/admin", tags=["administrador"])


def _producto_de_mi_sede_o_404(db: Session, producto_id: int, admin: models.Usuario) -> models.Producto:
    producto = db.query(models.Producto).filter(models.Producto.id == producto_id).first()
    if producto is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    if producto.sede_id != admin.sede_id:
        # HU-6: un admin solo puede operar sobre la sede que tiene asignada.
        raise HTTPException(
            status_code=403,
            detail="No puedes modificar productos de una sede distinta a la que administras",
        )
    return producto


@router.get("/inventario", response_model=List[schemas.ProductoOut])
def listar_inventario(
    db: Session = Depends(get_db),
    admin: models.Usuario = Depends(requerir_admin),
):
    """HU-10: consulta del inventario completo de la sede del administrador."""
    return (
        db.query(models.Producto)
        .filter(models.Producto.sede_id == admin.sede_id)
        .order_by(models.Producto.nombre)
        .all()
    )


@router.post("/productos", response_model=schemas.ProductoOut, status_code=201)
def crear_producto(
    datos: schemas.ProductoCreateRequest,
    db: Session = Depends(get_db),
    admin: models.Usuario = Depends(requerir_admin),
):
    """HU-7: agregar un producto nuevo al catálogo de la sede del administrador."""
    duplicado = db.query(models.Producto).filter(
        models.Producto.sede_id == admin.sede_id,
        models.Producto.sku == datos.sku,
    ).first()
    if duplicado:
        raise HTTPException(status_code=409, detail="Ya existe un producto con ese SKU en tu sede")

    producto = models.Producto(sede_id=admin.sede_id, **datos.model_dump())
    db.add(producto)
    db.commit()
    db.refresh(producto)
    return producto


@router.put("/productos/{producto_id}", response_model=schemas.ProductoOut)
def actualizar_producto(
    producto_id: int,
    datos: schemas.ProductoUpdateRequest,
    db: Session = Depends(get_db),
    admin: models.Usuario = Depends(requerir_admin),
):
    """HU-9: actualizar cantidad u otros datos de un producto existente."""
    producto = _producto_de_mi_sede_o_404(db, producto_id, admin)

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
    admin: models.Usuario = Depends(requerir_admin),
):
    """
    HU-8: eliminar un producto del catálogo.

    Se hace "soft delete" (activo=False) en vez de borrar la fila: así el
    historial de pedidos que ya incluían este producto se mantiene intacto,
    y el producto simplemente deja de aparecer en el catálogo del cliente
    y en el inventario activo del administrador.
    """
    producto = _producto_de_mi_sede_o_404(db, producto_id, admin)
    producto.activo = False
    db.commit()
    return {"mensaje": f"Producto '{producto.nombre}' eliminado del catálogo"}


@router.get("/perfil", response_model=schemas.UsuarioOut)
def perfil_admin(admin: models.Usuario = Depends(requerir_admin)):
    return admin
