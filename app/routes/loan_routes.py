"""
app/routes/loan_routes.py
--------------------------------------------------------------
Endpoints REST del recurso 'loans' (préstamos). A diferencia de
'users' y 'devices', este recurso conecta dos tablas mediante
ForeignKey, así que sus rutas validan explícitamente contra
user_service Y device_service antes de crear un préstamo.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.dependencies.database_dependency import get_db
from app.schemas.loan_schema import LoanCreate, LoanDetailResponse, LoanResponse
from app.services import device_service, loan_service, user_service

router = APIRouter(prefix="/loans", tags=["Loans"])


@router.get(
    "/",
    response_model=List[LoanResponse],
    summary="Listar préstamos",
    description="Lista préstamos, con filtros opcionales por estado, correo del usuario o tipo de dispositivo (estos dos últimos requieren un JOIN interno).",
    response_description="Lista de préstamos.",
)
def listar_prestamos(
    status_filter: Optional[str] = Query(default=None, alias="status", description="Filtra por estado: active, returned u overdue."),
    user_email: Optional[str] = Query(default=None, description="Filtra por el correo del usuario (requiere JOIN con users)."),
    device_type: Optional[str] = Query(default=None, description="Filtra por tipo de dispositivo (requiere JOIN con devices)."),
    db: Session = Depends(get_db),
):
    return loan_service.listar_prestamos(db, estado=status_filter, user_email=user_email, device_type=device_type)


@router.get(
    "/details",
    response_model=List[LoanDetailResponse],
    summary="Préstamos con información relacionada (JOIN)",
    description="Consulta avanzada: cada préstamo incluye los datos básicos del usuario y del dispositivo, obtenidos con un JOIN entre las 3 tablas.",
    response_description="Lista de préstamos con datos de usuario y dispositivo anidados.",
)
def listar_prestamos_detallados(
    status_filter: Optional[str] = Query(default=None, alias="status"),
    device_type: Optional[str] = Query(default=None),
    user_email: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    return loan_service.listar_prestamos_detallados(db, estado=status_filter, device_type=device_type, user_email=user_email)


@router.get(
    "/{loan_id}",
    response_model=LoanResponse,
    summary="Consultar un préstamo por su ID",
    description="Busca un préstamo por ID. 404 si no existe.",
    response_description="El préstamo encontrado.",
)
def obtener_prestamo(loan_id: int = Path(..., ge=1), db: Session = Depends(get_db)):
    prestamo = loan_service.obtener_prestamo_por_id(db, loan_id)
    if prestamo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Préstamo no encontrado")
    return prestamo


@router.post(
    "/",
    response_model=LoanResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un nuevo préstamo",
    description=(
        "Crea un préstamo, validando que el usuario exista, el dispositivo exista "
        "y esté disponible. Marca el dispositivo como no disponible."
    ),
    response_description="El préstamo recién creado.",
)
def crear_prestamo(datos: LoanCreate, db: Session = Depends(get_db)):
    usuario = user_service.obtener_usuario_por_id(db, datos.user_id)
    if usuario is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    dispositivo = device_service.obtener_dispositivo_por_id(db, datos.device_id)
    if dispositivo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dispositivo no encontrado")

    if not dispositivo.is_available:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"El dispositivo '{dispositivo.name}' no está disponible actualmente",
        )

    return loan_service.crear_prestamo(db, datos.user_id, datos.device_id)


@router.patch(
    "/{loan_id}/return",
    response_model=LoanResponse,
    summary="Registrar la devolución de un préstamo",
    description="Marca un préstamo como devuelto, asigna la fecha de devolución y libera el dispositivo. 404 si el préstamo no existe, 409 si ya estaba devuelto.",
    response_description="El préstamo actualizado con su estado 'returned'.",
)
def devolver_prestamo(loan_id: int = Path(..., ge=1), db: Session = Depends(get_db)):
    prestamo = loan_service.obtener_prestamo_por_id(db, loan_id)
    if prestamo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Préstamo no encontrado")

    if prestamo.status == "returned":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este préstamo ya había sido devuelto anteriormente",
        )

    return loan_service.devolver_prestamo(db, loan_id)
