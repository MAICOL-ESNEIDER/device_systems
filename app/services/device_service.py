"""
app/services/device_service.py
--------------------------------------------------------------
Lógica de negocio del recurso 'devices'. Mismo patrón que
user_service.py: funciones puras que reciben la sesión 'db' y no
saben nada de HTTP.
"""

from typing import Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.device_model import Device
from app.schemas.device_schema import DeviceCreate, DevicePatch, DeviceUpdate


def listar_dispositivos(
    db: Session,
    device_type: Optional[str] = None,
    is_available: Optional[bool] = None,
    brand: Optional[str] = None,
    search: Optional[str] = None,
) -> list[Device]:
    """Lista dispositivos con los 4 filtros opcionales que pide la guía."""
    query = db.query(Device)

    if device_type is not None:
        query = query.filter(Device.device_type == device_type)
    if is_available is not None:
        query = query.filter(Device.is_available == is_available)
    if brand is not None:
        query = query.filter(Device.brand.ilike(f"%{brand}%"))
    if search is not None:
        # 'search' busca coincidencias parciales (case-insensitive) en
        # nombre, número de serie o marca — una búsqueda de texto simple.
        patron = f"%{search}%"
        query = query.filter(
            or_(
                Device.name.ilike(patron),
                Device.serial_number.ilike(patron),
                Device.brand.ilike(patron),
            )
        )

    return query.all()


def obtener_dispositivo_por_id(db: Session, device_id: int) -> Optional[Device]:
    return db.query(Device).filter(Device.id == device_id).first()


def obtener_dispositivo_por_serial(db: Session, serial_number: str, excluir_id: Optional[int] = None) -> Optional[Device]:
    query = db.query(Device).filter(Device.serial_number == serial_number)
    if excluir_id is not None:
        query = query.filter(Device.id != excluir_id)
    return query.first()


def crear_dispositivo(db: Session, datos: DeviceCreate) -> Device:
    nuevo = Device(**datos.model_dump())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


def reemplazar_dispositivo(db: Session, device_id: int, datos: DeviceUpdate) -> Optional[Device]:
    dispositivo = obtener_dispositivo_por_id(db, device_id)
    if dispositivo is None:
        return None
    for campo, valor in datos.model_dump().items():
        setattr(dispositivo, campo, valor)
    db.commit()
    db.refresh(dispositivo)
    return dispositivo


def actualizar_dispositivo_parcial(db: Session, device_id: int, datos: DevicePatch) -> Optional[Device]:
    dispositivo = obtener_dispositivo_por_id(db, device_id)
    if dispositivo is None:
        return None
    for campo, valor in datos.model_dump(exclude_none=True).items():
        setattr(dispositivo, campo, valor)
    db.commit()
    db.refresh(dispositivo)
    return dispositivo


def eliminar_dispositivo(db: Session, device_id: int) -> bool:
    dispositivo = obtener_dispositivo_por_id(db, device_id)
    if dispositivo is None:
        return False
    db.delete(dispositivo)
    db.commit()
    return True
