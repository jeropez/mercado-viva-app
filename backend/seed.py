"""
Datos semilla para poder demostrar el flujo completo sin depender de que
un administrador cargue productos manualmente primero.

Las imágenes usan Unsplash Source como placeholders de ejemplo (enlaces
directos), ya que el catálogo guarda URLs de imagen, no archivos subidos.
Reemplázalas por las fotos reales de cada producto cuando las tengan.
"""
from sqlalchemy.orm import Session
import models
from database import SessionLocal, engine, Base


def cargar_datos_semilla():
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    try:
        if db.query(models.Sede).count() > 0:
            return  # ya hay datos, no duplicar

        sede_laureles = models.Sede(
            nombre="Mercado VIVA Laureles", ciudad="Medellín",
            direccion="Cra 70 # 34-12"
        )
        sede_poblado = models.Sede(
            nombre="Mercado VIVA Poblado", ciudad="Medellín",
            direccion="Cl 10 # 40-05"
        )
        db.add_all([sede_laureles, sede_poblado])
        db.commit()
        db.refresh(sede_laureles)
        db.refresh(sede_poblado)

        productos = [
            # --- Laureles ---
            dict(sede_id=sede_laureles.id, sku="ARR-001", nombre="Arroz Diana 1kg",
                 descripcion="Arroz blanco premium, bolsa de 1 kilogramo.",
                 categoria="Abarrotes", precio=4500, cantidad=2,
                 imagen_url="https://images.unsplash.com/photo-1586201375761-83865001e31c?w=500"),
            dict(sede_id=sede_laureles.id, sku="ACE-001", nombre="Aceite Girasol 1L",
                 descripcion="Aceite vegetal de girasol, botella de 1 litro.",
                 categoria="Abarrotes", precio=12500, cantidad=10,
                 imagen_url="https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=500"),
            dict(sede_id=sede_laureles.id, sku="LEC-001", nombre="Leche Entera 1L",
                 descripcion="Leche entera pasteurizada, caja de 1 litro.",
                 categoria="Lácteos", precio=3800, cantidad=0,
                 imagen_url="https://images.unsplash.com/photo-1550583724-b2692b85b150?w=500"),
            dict(sede_id=sede_laureles.id, sku="PAN-001", nombre="Panela Redonda 500g",
                 descripcion="Panela artesanal en presentación redonda de 500 gramos.",
                 categoria="Abarrotes", precio=3200, cantidad=15,
                 imagen_url="https://images.unsplash.com/photo-1631206753348-db44968fd440?w=500"),
            dict(sede_id=sede_laureles.id, sku="CAF-001", nombre="Café Molido 500g",
                 descripcion="Café colombiano molido, tueste medio.",
                 categoria="Abarrotes", precio=15900, cantidad=8,
                 imagen_url="https://images.unsplash.com/photo-1509042239860-f550ce710b93?w=500"),
            dict(sede_id=sede_laureles.id, sku="HUE-001", nombre="Huevos AA x30",
                 descripcion="Cubeta de 30 huevos rojos tipo AA.",
                 categoria="Lácteos", precio=17500, cantidad=0,
                 imagen_url="https://images.unsplash.com/photo-1582722872445-44dc5f7e3c8f?w=500"),

            # --- Poblado ---
            dict(sede_id=sede_poblado.id, sku="ARR-001", nombre="Arroz Diana 1kg",
                 descripcion="Arroz blanco premium, bolsa de 1 kilogramo.",
                 categoria="Abarrotes", precio=4600, cantidad=20,
                 imagen_url="https://images.unsplash.com/photo-1586201375761-83865001e31c?w=500"),
            dict(sede_id=sede_poblado.id, sku="ACE-001", nombre="Aceite Girasol 1L",
                 descripcion="Aceite vegetal de girasol, botella de 1 litro.",
                 categoria="Abarrotes", precio=12900, cantidad=8,
                 imagen_url="https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=500"),
            dict(sede_id=sede_poblado.id, sku="LEC-001", nombre="Leche Entera 1L",
                 descripcion="Leche entera pasteurizada, caja de 1 litro.",
                 categoria="Lácteos", precio=3900, cantidad=12,
                 imagen_url="https://images.unsplash.com/photo-1550583724-b2692b85b150?w=500"),
            dict(sede_id=sede_poblado.id, sku="QUE-001", nombre="Queso Campesino 500g",
                 descripcion="Queso campesino fresco, bloque de 500 gramos.",
                 categoria="Lácteos", precio=11200, cantidad=6,
                 imagen_url="https://images.unsplash.com/photo-1486297678162-eb2a19b0a32d?w=500"),
            dict(sede_id=sede_poblado.id, sku="PAN-002", nombre="Pan Tajado Integral",
                 descripcion="Pan tajado integral, paquete de 500 gramos.",
                 categoria="Panadería", precio=6300, cantidad=10,
                 imagen_url="https://images.unsplash.com/photo-1509440159596-0249088772ff?w=500"),
        ]

        for p in productos:
            db.add(models.Producto(**p))

        db.commit()
        print("Datos semilla cargados: 2 sedes, 11 productos.")
    finally:
        db.close()


if __name__ == "__main__":
    cargar_datos_semilla()
