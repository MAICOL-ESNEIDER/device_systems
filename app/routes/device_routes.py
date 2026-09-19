"""
app/routes/device_routes.py
--------------------------------------------------------------
Endpoints REST del recurso 'devices'. Mismo patrón que
user_routes.py: CRUD completo (GET, GET/id, POST, PUT, PATCH,
DELETE) más filtros de listado, y un endpoint adicional para
consultar el historial de préstamos de un dispositivo (join con
'loans', ver Fase 10 de la guía).
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.dependencies.database_dependency import get_db
from app.schemas.device_schema import DeviceCreate, DevicePatch, DeviceResponse, DeviceUpdate
from app.schemas.loan_schema import LoanResponse
from app.services import device_service, loan_service

router = APIRouter(prefix="/devices", tags=["Devices"])


def get_device_or_404(
    device_id: int = Path(..., description="ID del dispositivo", ge=1),
    db: Session = Depends(get_db),
):
    """Dependencia reutilizable: busca un dispositivo por ID; 404 si no existe."""
    dispositivo = device_service.obtener_dispositivo_por_id(db, device_id)
    if dispositivo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dispositivo no encontrado")
    return dispositivo


@router.get(
    "/",
    response_model=List[DeviceResponse],
    summary="Listar dispositivos",
    description="Lista dispositivos con filtros opcionales por tipo, disponibilidad, marca, o búsqueda de texto libre.",
    response_description="Lista de dispositivos.",
)
def listar_dispositivos(
    device_type: Optional[str] = Query(default=None, description="Filtra por tipo: laptop, tablet, proyector, etc."),
    is_available: Optional[bool] = Query(default=None, description="Filtra por disponibilidad."),
    brand: Optional[str] = Query(default=None, description="Filtra por marca (coincidencia parcial)."),
    search: Optional[str] = Query(default=None, description="Busca en nombre, número de serie o marca."),
    db: Session = Depends(get_db),
):
    return device_service.listar_dispositivos(db, device_type=device_type, is_available=is_available, brand=brand, search=search)


@router.get(
    "/{device_id}",
    response_model=DeviceResponse,
    summary="Consultar un dispositivo por su ID",
    description="Busca un dispositivo por ID. 404 si no existe.",
    response_description="El dispositivo encontrado.",
)
def obtener_dispositivo(dispositivo=Depends(get_device_or_404)):
    return dispositivo


@router.get(
    "/{device_id}/loans",
    response_model=List[LoanResponse],
    summary="Historial de préstamos de un dispositivo",
    description="Lista todos los préstamos (activos e históricos) asociados a un dispositivo.",
    response_description="Lista de préstamos del dispositivo.",
)
def historial_prestamos_dispositivo(
    dispositivo=Depends(get_device_or_404),
    db: Session = Depends(get_db),
):
    return loan_service.listar_prestamos_por_dispositivo(db, dispositivo.id)


@router.post(
    "/",
    response_model=DeviceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un nuevo dispositivo",
    description="Crea un dispositivo. Rechaza números de serie duplicados.",
    response_description="El dispositivo recién creado.",
)
def crear_dispositivo(dispositivo: DeviceCreate, db: Session = Depends(get_db)):
    if device_service.obtener_dispositivo_por_serial(db, dispositivo.serial_number) is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe un dispositivo registrado con el número de serie '{dispositivo.serial_number}'",
        )
    return device_service.crear_dispositivo(db, dispositivo)


@router.put(
    "/{device_id}",
    response_model=DeviceResponse,
    summary="Actualizar un dispositivo por completo",
    description="Reemplaza todos los campos de un dispositivo. 404 si no existe, 400 si el serial pertenece a otro.",
    response_description="El dispositivo actualizado.",
)
def reemplazar_dispositivo(
    datos: DeviceUpdate,
    dispositivo_actual=Depends(get_device_or_404),
    db: Session = Depends(get_db),
):
    serial_en_uso = device_service.obtener_dispositivo_por_serial(db, datos.serial_number, excluir_id=dispositivo_actual.id)
    if serial_en_uso is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe otro dispositivo con el número de serie '{datos.serial_number}'",
        )
    return device_service.reemplazar_dispositivo(db, dispositivo_actual.id, datos)


@router.patch(
    "/{device_id}",
    response_model=DeviceResponse,
    summary="Actualizar un dispositivo parcialmente",
    description="Modifica solo los campos enviados. 404 si no existe.",
    response_description="El dispositivo actualizado.",
)
def actualizar_dispositivo_parcial(
    datos: DevicePatch,
    dispositivo_actual=Depends(get_device_or_404),
    db: Session = Depends(get_db),
):
    return device_service.actualizar_dispositivo_parcial(db, dispositivo_actual.id, datos)


@router.delete(
    "/{device_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un dispositivo",
    description="Elimina un dispositivo. 404 si no existe.",
    response_description="Sin contenido.",
)
def eliminar_dispositivo(dispositivo_actual=Depends(get_device_or_404), db: Session = Depends(get_db)) -> None:
    device_service.eliminar_dispositivo(db, dispositivo_actual.id)
    return None
