from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db
from auth import requerir_cliente

router = APIRouter(prefix="/api", tags=["cliente"])


# ---------------------------------------------------------------------------
# Catálogo (público, no requiere sesión — igual que navegar un marketplace)
# ---------------------------------------------------------------------------

@router.get("/productos", response_model=List[schemas.ProductoOut])
def listar_catalogo(
    sede_id: int = Query(..., gt=0),
    categoria: Optional[str] = None,
    q: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(models.Producto).filter(
        models.Producto.sede_id == sede_id,
        models.Producto.activo == True,  # noqa: E712
    )
    if categoria:
        query = query.filter(models.Producto.categoria == categoria)
    if q:
        query = query.filter(models.Producto.nombre.ilike(f"%{q}%"))

    return query.order_by(models.Producto.nombre).all()


@router.get("/productos/{producto_id}", response_model=schemas.ProductoOut)
def detalle_producto(producto_id: int, db: Session = Depends(get_db)):
    producto = db.query(models.Producto).filter(
        models.Producto.id == producto_id, models.Producto.activo == True  # noqa: E712
    ).first()
    if producto is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return producto


def _buscar_alternativas(db: Session, producto: models.Producto) -> List[schemas.ProductoAlternativaOut]:
    """
    HU-5: cuando un producto no tiene stock, se sugiere:
      1) el mismo producto (mismo nombre) disponible en otra sede, y
      2) productos de la misma categoría con stock en la misma sede.
    """
    alternativas: List[schemas.ProductoAlternativaOut] = []

    # 1) Misma referencia en otra sede
    otras_sedes = (
        db.query(models.Producto)
        .filter(
            models.Producto.nombre == producto.nombre,
            models.Producto.sede_id != producto.sede_id,
            models.Producto.cantidad > 0,
            models.Producto.activo == True,  # noqa: E712
        )
        .all()
    )
    for alt in otras_sedes:
        alternativas.append(schemas.ProductoAlternativaOut(
            id=alt.id, nombre=alt.nombre, precio=alt.precio, cantidad=alt.cantidad,
            imagen_url=alt.imagen_url, sede_id=alt.sede_id, sede_nombre=alt.sede.nombre,
            tipo_alternativa="otra_sede_mismo_producto",
        ))

    # 2) Misma categoría, misma sede, con stock
    misma_categoria = (
        db.query(models.Producto)
        .filter(
            models.Producto.categoria == producto.categoria,
            models.Producto.sede_id == producto.sede_id,
            models.Producto.id != producto.id,
            models.Producto.cantidad > 0,
            models.Producto.activo == True,  # noqa: E712
        )
        .limit(3)
        .all()
    )
    for alt in misma_categoria:
        alternativas.append(schemas.ProductoAlternativaOut(
            id=alt.id, nombre=alt.nombre, precio=alt.precio, cantidad=alt.cantidad,
            imagen_url=alt.imagen_url, sede_id=alt.sede_id, sede_nombre=alt.sede.nombre,
            tipo_alternativa="misma_sede_categoria",
        ))

    return alternativas


# ---------------------------------------------------------------------------
# Checkout (requiere sesión de cliente) — HU-4 (descuento inmediato) + HU-5
# ---------------------------------------------------------------------------

@router.post("/cliente/checkout", response_model=schemas.CheckoutResponse)
def checkout(
    datos: schemas.CheckoutRequest,
    db: Session = Depends(get_db),
    cliente: models.Usuario = Depends(requerir_cliente),
):
    sede = db.query(models.Sede).filter(models.Sede.id == datos.sede_id).first()
    if sede is None:
        raise HTTPException(status_code=404, detail="La sede indicada no existe")

    productos_por_id = {}
    items_sin_stock = []

    # 1) Verificar TODO el carrito antes de tocar la base de datos (todo o nada)
    for item in datos.items:
        producto = db.query(models.Producto).filter(
            models.Producto.id == item.producto_id,
            models.Producto.sede_id == datos.sede_id,
            models.Producto.activo == True,  # noqa: E712
        ).first()

        if producto is None:
            raise HTTPException(
                status_code=404,
                detail=f"El producto {item.producto_id} no existe en la sede seleccionada",
            )

        productos_por_id[item.producto_id] = producto

        if producto.cantidad < item.cantidad:
            items_sin_stock.append(schemas.CheckoutSinStockItem(
                producto_id=producto.id,
                producto_nombre=producto.nombre,
                cantidad_solicitada=item.cantidad,
                cantidad_disponible=producto.cantidad,
                alternativas=_buscar_alternativas(db, producto),
            ))

    # 2) Si algo no tiene stock, no se cobra nada ni se crea el pedido
    if items_sin_stock:
        return schemas.CheckoutResponse(
            resultado="sin_stock",
            mensaje="Uno o más productos no tienen stock suficiente. No se realizó ningún cobro.",
            items_sin_stock=items_sin_stock,
        )

    # 3) Hay stock de todo: se descuenta de inmediato y se registra el pedido
    subtotal = sum(productos_por_id[i.producto_id].precio * i.cantidad for i in datos.items)

    pedido = models.Pedido(
        cliente_id=cliente.id,
        sede_id=datos.sede_id,
        estado="confirmado",
        subtotal=subtotal,
        total=subtotal,  # el MVP no calcula envío/impuestos por separado
        nombre_facturacion=datos.nombre_facturacion,
        documento_facturacion=datos.documento_facturacion,
        direccion_facturacion=datos.direccion_facturacion,
        ciudad_facturacion=datos.ciudad_facturacion,
        direccion_envio=datos.direccion_envio,
        ciudad_envio=datos.ciudad_envio,
        telefono_contacto=datos.telefono_contacto,
    )
    db.add(pedido)
    db.flush()  # para obtener pedido.id antes del commit

    for item in datos.items:
        producto = productos_por_id[item.producto_id]
        producto.cantidad -= item.cantidad  # <-- actualización de inventario en tiempo real

        db.add(models.PedidoItem(
            pedido_id=pedido.id,
            producto_id=producto.id,
            producto_nombre=producto.nombre,
            precio_unitario=producto.precio,
            cantidad=item.cantidad,
        ))

    db.commit()
    db.refresh(pedido)

    return schemas.CheckoutResponse(
        resultado="confirmado",
        mensaje=f"Pedido #{pedido.id} confirmado.",
        pedido=pedido,
    )


@router.get("/cliente/pedidos", response_model=List[schemas.PedidoOut])
def historial_pedidos(
    db: Session = Depends(get_db),
    cliente: models.Usuario = Depends(requerir_cliente),
):
    return (
        db.query(models.Pedido)
        .filter(models.Pedido.cliente_id == cliente.id)
        .order_by(models.Pedido.creado_en.desc())
        .all()
    )
