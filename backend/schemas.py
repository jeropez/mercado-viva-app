from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, field_validator


# ---------------------------------------------------------------------------
# Sedes
# ---------------------------------------------------------------------------

class SedeOut(BaseModel):
    id: int
    nombre: str
    ciudad: str
    direccion: Optional[str] = None

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Autenticación / usuarios
# ---------------------------------------------------------------------------

class RegistroClienteRequest(BaseModel):
    nombres: str = Field(..., min_length=2, max_length=120)
    apellidos: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    documento: str = Field(..., min_length=4, max_length=30)
    telefono: Optional[str] = Field(None, max_length=30)
    direccion: Optional[str] = Field(None, max_length=200)
    ciudad: Optional[str] = Field(None, max_length=80)
    password: str = Field(..., min_length=6, max_length=100)


class RegistroAdminRequest(BaseModel):
    nombres: str = Field(..., min_length=2, max_length=120)
    apellidos: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    documento: str = Field(..., min_length=4, max_length=30)
    telefono: Optional[str] = Field(None, max_length=30)
    password: str = Field(..., min_length=6, max_length=100)
    sede_id: int = Field(..., gt=0, description="Sede que este administrador va a gestionar")


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UsuarioOut(BaseModel):
    id: int
    tipo: str
    nombres: str
    apellidos: str
    email: str
    documento: str
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    ciudad: Optional[str] = None
    sede_id: Optional[int] = None

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioOut


# ---------------------------------------------------------------------------
# Productos (catálogo / inventario)
# ---------------------------------------------------------------------------

class ProductoOut(BaseModel):
    id: int
    sede_id: int
    sku: str
    nombre: str
    descripcion: Optional[str] = None
    categoria: str
    precio: float
    cantidad: int
    imagen_url: Optional[str] = None
    activo: bool

    class Config:
        from_attributes = True


class ProductoAlternativaOut(BaseModel):
    id: int
    nombre: str
    precio: float
    cantidad: int
    imagen_url: Optional[str] = None
    sede_id: int
    sede_nombre: str
    tipo_alternativa: str  # "misma_sede_categoria" | "otra_sede_mismo_producto"


class ProductoCreateRequest(BaseModel):
    sku: str = Field(..., min_length=2, max_length=40)
    nombre: str = Field(..., min_length=2, max_length=160)
    descripcion: Optional[str] = Field(None, max_length=2000)
    categoria: str = Field("General", max_length=80)
    precio: float = Field(..., gt=0)
    cantidad: int = Field(..., ge=0)
    imagen_url: Optional[str] = Field(None, max_length=400)


class ProductoUpdateRequest(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=160)
    descripcion: Optional[str] = Field(None, max_length=2000)
    categoria: Optional[str] = Field(None, max_length=80)
    precio: Optional[float] = Field(None, gt=0)
    cantidad: Optional[int] = Field(None, ge=0)
    imagen_url: Optional[str] = Field(None, max_length=400)


# ---------------------------------------------------------------------------
# Checkout / pedidos
# ---------------------------------------------------------------------------

class ItemCarrito(BaseModel):
    producto_id: int = Field(..., gt=0)
    cantidad: int = Field(..., gt=0)


class CheckoutRequest(BaseModel):
    sede_id: int = Field(..., gt=0)
    items: List[ItemCarrito] = Field(..., min_length=1)

    # Datos de facturación
    nombre_facturacion: str = Field(..., min_length=2, max_length=160)
    documento_facturacion: str = Field(..., min_length=4, max_length=30)
    direccion_facturacion: str = Field(..., min_length=4, max_length=200)
    ciudad_facturacion: str = Field(..., min_length=2, max_length=80)

    # Datos de residencia / envío
    direccion_envio: str = Field(..., min_length=4, max_length=200)
    ciudad_envio: str = Field(..., min_length=2, max_length=80)
    telefono_contacto: str = Field(..., min_length=6, max_length=30)


class PedidoItemOut(BaseModel):
    producto_nombre: str
    precio_unitario: float
    cantidad: int

    class Config:
        from_attributes = True


class PedidoOut(BaseModel):
    id: int
    sede_id: int
    estado: str
    subtotal: float
    total: float
    creado_en: datetime
    direccion_envio: str
    ciudad_envio: str
    items: List[PedidoItemOut]

    class Config:
        from_attributes = True


class CheckoutSinStockItem(BaseModel):
    producto_id: int
    producto_nombre: str
    cantidad_solicitada: int
    cantidad_disponible: int
    alternativas: List[ProductoAlternativaOut]


class CheckoutResponse(BaseModel):
    resultado: str  # "confirmado" | "sin_stock"
    pedido: Optional[PedidoOut] = None
    mensaje: Optional[str] = None
    items_sin_stock: Optional[List[CheckoutSinStockItem]] = None
