"""
app/schemas/loan_schema.py
--------------------------------------------------------------
Schemas Pydantic del recurso 'loans'. Incluye LoanDetailResponse,
que muestra información relacionada del usuario y del dispositivo
en una sola respuesta (usado por las consultas con joins).
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class LoanCreate(BaseModel):
    """Entrada para POST /loans: solo se necesita saber quién y qué dispositivo."""

    user_id: int = Field(..., description="ID del usuario que solicita el préstamo.")
    device_id: int = Field(..., description="ID del dispositivo a prestar.")


class LoanUpdate(BaseModel):
    """
    Schema de uso interno para modificar un préstamo (status y/o
    return_date). No se expone en un endpoint genérico PUT/PATCH:
    la única forma pública de cambiar un préstamo es el endpoint
    específico PATCH /loans/{loan_id}/return, que internamente usa
    esta estructura para aplicar el cambio de forma controlada.
    """

    status: Optional[str] = None
    return_date: Optional[datetime] = None


class LoanResponse(BaseModel):
    """Salida simple de un préstamo (sin datos anidados de usuario/dispositivo)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    device_id: int
    loan_date: datetime
    return_date: Optional[datetime] = None
    status: str


class LoanUserSummary(BaseModel):
    """Datos básicos del usuario, para anidar dentro de LoanDetailResponse."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str


class LoanDeviceSummary(BaseModel):
    """Datos básicos del dispositivo, para anidar dentro de LoanDetailResponse."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    serial_number: str
    device_type: str


class LoanDetailResponse(BaseModel):
    """
    Salida "enriquecida" de un préstamo: en vez de solo los IDs de
    usuario y dispositivo, incluye sus datos básicos ya resueltos.
    Se arma en la capa de servicio a partir de una consulta con JOIN
    (ver loan_service.listar_prestamos_detallados()).
    """

    loan_id: int
    status: str
    loan_date: datetime
    return_date: Optional[datetime] = None
    user: LoanUserSummary
    device: LoanDeviceSummary
