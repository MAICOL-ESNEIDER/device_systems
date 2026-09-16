"""
app/schemas/user_schema.py
--------------------------------------------------------------
Schemas Pydantic del recurso 'users'. Definen el CONTRATO de
entrada/salida de la API: qué puede enviar un cliente y qué recibe
de vuelta. No representan la tabla de la base de datos (eso lo hace
app/models/user_model.py) — ver la diferencia explicada en el README.

Nombres usados en esta versión (EV09), según la guía:
- UserCreate: entrada para POST.
- UserUpdate: entrada para PUT (reemplazo completo).
- UserPatch:  entrada para PATCH (actualización parcial).
- UserResponse: salida de la API.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRole(str, Enum):
    admin = "admin"
    support = "support"
    user = "user"


class UserBase(BaseModel):
    name: str = Field(..., min_length=3, description="Nombre completo del usuario (mínimo 3 caracteres).")
    email: EmailStr = Field(..., description="Correo electrónico del usuario.")
    role: UserRole = Field(..., description="Rol del usuario: admin, support o user.")
    is_active: bool = Field(default=True, description="Indica si el usuario está activo.")


class UserCreate(UserBase):
    """Entrada para POST /users."""

    pass


class UserUpdate(BaseModel):
    """Entrada para PUT /users/{user_id}: reemplazo COMPLETO, todos los campos obligatorios."""

    name: str = Field(..., min_length=3)
    email: EmailStr
    role: UserRole
    is_active: bool


class UserPatch(BaseModel):
    """Entrada para PATCH /users/{user_id}: actualización PARCIAL, todos los campos opcionales."""

    name: Optional[str] = Field(default=None, min_length=3)
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """
    Salida de la API. 'model_config = ConfigDict(from_attributes=True)'
    permite construir este schema directamente desde un objeto ORM
    (User de SQLAlchemy) en vez de solo desde un diccionario — necesario
    porque ahora los datos vienen de la base de datos, no de una lista
    en memoria como en EV07/EV08.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
