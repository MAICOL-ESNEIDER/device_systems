"""
app/schemas/device_schema.py
--------------------------------------------------------------
Schemas Pydantic del recurso 'devices'. Sigue el mismo patrón que
user_schema.py: un schema de entrada por operación (Create/Update
completo/Patch parcial) y uno de salida (Response).
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class DeviceBase(BaseModel):
    name: str = Field(..., min_length=2, description="Nombre descriptivo del dispositivo.")
    serial_number: str = Field(..., min_length=3, description="Número de serie único del dispositivo.")
    device_type: str = Field(..., description="Tipo de dispositivo: laptop, tablet, proyector, cámara, router, monitor, etc.")
    brand: Optional[str] = Field(default=None, description="Marca del dispositivo (opcional).")
    is_available: bool = Field(default=True, description="Indica si el dispositivo está disponible para préstamo.")


class DeviceCreate(DeviceBase):
    """Entrada para POST /devices."""

    pass


class DeviceUpdate(BaseModel):
    """Entrada para PUT /devices/{device_id}: reemplazo COMPLETO."""

    name: str = Field(..., min_length=2)
    serial_number: str = Field(..., min_length=3)
    device_type: str
    brand: Optional[str] = None
    is_available: bool


class DevicePatch(BaseModel):
    """
    Entrada para PATCH /devices/{device_id}: actualización PARCIAL.
    No estaba en la lista de schemas sugeridos por la guía (solo
    menciona DeviceCreate/DeviceUpdate/DeviceResponse), pero se agrega
    para mantener la misma semántica PUT-vs-PATCH ya usada en 'users'
    (todos los campos opcionales, se actualiza solo lo enviado).
    """

    name: Optional[str] = Field(default=None, min_length=2)
    serial_number: Optional[str] = Field(default=None, min_length=3)
    device_type: Optional[str] = None
    brand: Optional[str] = None
    is_available: Optional[bool] = None


class DeviceResponse(DeviceBase):
    """Salida de la API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
