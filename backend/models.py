"""
Modelos de datos de Mercado VIVA.

Diseño relacional pensado para el enfoque de gestión de inventario con
dos roles (cliente / administrador), donde cada administrador gestiona
el catálogo de UNA sede, y cada cliente compra desde el catálogo de una
sede específica.
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Text
)
from sqlalchemy.orm import relationship
from database import Base


class Sede(Base):
    __tablename__ = "sedes"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(120), unique=True, nullable=False)
    ciudad = Column(String(80), nullable=False)
    direccion = Column(String(200), nullable=True)

    productos = relationship("Producto", back_populates="sede")
    administradores = relationship("Usuario", back_populates="sede")


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(String(20), nullable=False)  # "cliente" | "admin"

    nombres = Column(String(120), nullable=False)
    apellidos = Column(String(120), nullable=False)
    email = Column(String(160), unique=True, nullable=False, index=True)
    documento = Column(String(30), unique=True, nullable=False, index=True)
    telefono = Column(String(30), nullable=True)
    password_hash = Column(String(255), nullable=False)

    # Solo aplica a clientes (dirección de residencia por defecto, editable en el checkout)
    direccion = Column(String(200), nullable=True)
    ciudad = Column(String(80), nullable=True)

    # Solo aplica a administradores: la sede que gestionan
    sede_id = Column(Integer, ForeignKey("sedes.id"), nullable=True)
    sede = relationship("Sede", back_populates="administradores")

    creado_en = Column(DateTime, default=datetime.utcnow)

    pedidos = relationship("Pedido", back_populates="cliente")


class Producto(Base):
    __tablename__ = "productos"

    id = Column(Integer, primary_key=True, index=True)
    sede_id = Column(Integer, ForeignKey("sedes.id"), nullable=False)

    sku = Column(String(40), nullable=False)
    nombre = Column(String(160), nullable=False)
    descripcion = Column(Text, nullable=True)
    categoria = Column(String(80), nullable=False, default="General")
    precio = Column(Float, nullable=False)
    cantidad = Column(Integer, nullable=False, default=0)

    # URL de la imagen del producto. En el MVP se ingresa como enlace
    # (no hay almacenamiento de archivos persistente en Render por defecto).
    imagen_url = Column(String(400), nullable=True)

    activo = Column(Boolean, default=True)
    creado_en = Column(DateTime, default=datetime.utcnow)

    sede = relationship("Sede", back_populates="productos")


class Pedido(Base):
    __tablename__ = "pedidos"

    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    sede_id = Column(Integer, ForeignKey("sedes.id"), nullable=False)

    estado = Column(String(30), nullable=False, default="confirmado")
    subtotal = Column(Float, nullable=False)
    total = Column(Float, nullable=False)
    creado_en = Column(DateTime, default=datetime.utcnow)

    # --- Datos de facturación ---
    nombre_facturacion = Column(String(160), nullable=False)
    documento_facturacion = Column(String(30), nullable=False)
    direccion_facturacion = Column(String(200), nullable=False)
    ciudad_facturacion = Column(String(80), nullable=False)

    # --- Datos de residencia / envío ---
    direccion_envio = Column(String(200), nullable=False)
    ciudad_envio = Column(String(80), nullable=False)
    telefono_contacto = Column(String(30), nullable=False)

    cliente = relationship("Usuario", back_populates="pedidos")
    sede = relationship("Sede")
    items = relationship("PedidoItem", back_populates="pedido", cascade="all, delete-orphan")


class PedidoItem(Base):
    __tablename__ = "pedido_items"

    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id"), nullable=False)

    # Nullable + SET NULL: si el admin elimina el producto después de la compra,
    # el historial del pedido no se rompe, solo pierde el enlace al catálogo vivo.
    producto_id = Column(Integer, ForeignKey("productos.id", ondelete="SET NULL"), nullable=True)

    # Snapshot del producto al momento de comprar (para que el historial
    # nunca cambie aunque el admin edite precio o elimine el producto después).
    producto_nombre = Column(String(160), nullable=False)
    precio_unitario = Column(Float, nullable=False)
    cantidad = Column(Integer, nullable=False)

    pedido = relationship("Pedido", back_populates="items")
