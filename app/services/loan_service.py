"""
app/services/loan_service.py
--------------------------------------------------------------
Lógica de negocio del recurso 'loans' (préstamos). Incluye las
consultas con JOIN que combinan información de las 3 tablas
(users, devices, loans) para las respuestas detalladas y los
filtros avanzados.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models.device_model import Device
from app.models.loan_model import Loan
from app.models.user_model import User


def crear_prestamo(db: Session, user_id: int, device_id: int) -> Loan:
    """
    Crea el registro de préstamo y marca el dispositivo como no
    disponible. La validación de que el usuario exista, el
    dispositivo exista y esté disponible se hace en la ruta (usa
    user_service y device_service), porque cruza dos recursos
    distintos y no es responsabilidad exclusiva de 'loans'.
    """
    nuevo_prestamo = Loan(user_id=user_id, device_id=device_id, status="active")
    db.add(nuevo_prestamo)

    dispositivo = db.query(Device).filter(Device.id == device_id).first()
    dispositivo.is_available = False

    db.commit()
    db.refresh(nuevo_prestamo)
    return nuevo_prestamo


def devolver_prestamo(db: Session, loan_id: int) -> Optional[Loan]:
    """
    Marca un préstamo como devuelto: asigna return_date, cambia
    status a 'returned' y vuelve a poner el dispositivo como
    disponible. Devuelve None si el préstamo no existe.
    """
    prestamo = obtener_prestamo_por_id(db, loan_id)
    if prestamo is None:
        return None

    prestamo.status = "returned"
    prestamo.return_date = datetime.utcnow()

    dispositivo = db.query(Device).filter(Device.id == prestamo.device_id).first()
    dispositivo.is_available = True

    db.commit()
    db.refresh(prestamo)
    return prestamo


def obtener_prestamo_por_id(db: Session, loan_id: int) -> Optional[Loan]:
    return db.query(Loan).filter(Loan.id == loan_id).first()


def listar_prestamos(
    db: Session,
    estado: Optional[str] = None,
    user_email: Optional[str] = None,
    device_type: Optional[str] = None,
) -> list[Loan]:
    """
    Lista préstamos con filtros opcionales. Cuando se filtra por
    'user_email' o 'device_type' (campos que NO viven en la tabla
    'loans'), se hace un JOIN hacia 'users' o 'devices' para poder
    filtrar por esos campos.
    """
    query = db.query(Loan)

    if estado is not None:
        query = query.filter(Loan.status == estado)
    if user_email is not None:
        query = query.join(User, Loan.user_id == User.id).filter(User.email == user_email)
    if device_type is not None:
        query = query.join(Device, Loan.device_id == Device.id).filter(Device.device_type == device_type)

    return query.all()


def listar_prestamos_por_usuario(db: Session, user_id: int) -> list[Loan]:
    return db.query(Loan).filter(Loan.user_id == user_id).all()


def listar_prestamos_por_dispositivo(db: Session, device_id: int) -> list[Loan]:
    return db.query(Loan).filter(Loan.device_id == device_id).all()


def listar_prestamos_detallados(
    db: Session,
    estado: Optional[str] = None,
    device_type: Optional[str] = None,
    user_email: Optional[str] = None,
) -> list[dict]:
    """
    Consulta con JOIN explícito entre 'loans', 'users' y 'devices',
    para armar la respuesta enriquecida (LoanDetailResponse) que
    muestra los datos del usuario y del dispositivo junto al
    préstamo, en una sola respuesta.
    """
    query = (
        db.query(Loan, User, Device)
        .join(User, Loan.user_id == User.id)
        .join(Device, Loan.device_id == Device.id)
    )

    if estado is not None:
        query = query.filter(Loan.status == estado)
    if device_type is not None:
        query = query.filter(Device.device_type == device_type)
    if user_email is not None:
        query = query.filter(User.email == user_email)

    resultados = []
    for prestamo, usuario, dispositivo in query.all():
        resultados.append(
            {
                "loan_id": prestamo.id,
                "status": prestamo.status,
                "loan_date": prestamo.loan_date,
                "return_date": prestamo.return_date,
                "user": {"id": usuario.id, "name": usuario.name, "email": usuario.email},
                "device": {
                    "id": dispositivo.id,
                    "name": dispositivo.name,
                    "serial_number": dispositivo.serial_number,
                    "device_type": dispositivo.device_type,
                },
            }
        )
    return resultados
