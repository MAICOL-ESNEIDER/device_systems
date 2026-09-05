"""
app/schemas/user_schema.py
--------------------------------------------------------------
Modelos Pydantic para validar los datos de usuario que entran y
salen de la API. Esta versión (EV08) añade dos modelos de entrada
nuevos, uno por cada tipo de actualización:

- UserReplace (PUT):   todos los campos son obligatorios, porque
  un PUT reemplaza el recurso completo.
- UserUpdate  (PATCH): todos los campos son opcionales, porque un
  PATCH solo debe tocar los campos que el cliente decida enviar.
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserRole(str, Enum):
    """
    Roles permitidos para un usuario del sistema. Heredar de
    (str, Enum) hace que FastAPI valide automáticamente el valor
    recibido y lo muestre como texto simple en Swagger.
    """

    admin = "admin"
    support = "support"
    user = "user"


class UserBase(BaseModel):
    """Campos que comparten la creación y la respuesta de un usuario."""

    name: str = Field(
        ..., min_length=3,
        description="Nombre completo del usuario (mínimo 3 caracteres).",
        examples=["Camila Restrepo"],
    )
    email: EmailStr = Field(
        ..., description="Correo electrónico del usuario. Debe tener un formato válido.",
        examples=["camila@ejemplo.com"],
    )
    role: UserRole = Field(
        ..., description="Rol del usuario dentro del sistema: admin, support o user.",
        examples=["user"],
    )
    is_active: bool = Field(
        default=True, description="Indica si el usuario está activo en el sistema.",
    )


class UserCreate(UserBase):
    """Modelo de ENTRADA para POST /users. No incluye 'id' (lo asigna el servidor)."""

    pass


class UserReplace(BaseModel):
    """
    Modelo de ENTRADA para PUT /users/{user_id}: actualización COMPLETA.

    A diferencia de UserBase, aquí 'is_active' es obligatorio (sin
    valor por defecto): el estándar REST para PUT es reemplazar el
    recurso entero, así que el cliente debe enviar TODOS los campos,
    no puede dejar ninguno "como estaba antes".
    """

    name: str = Field(..., min_length=3, description="Nombre completo del usuario (mínimo 3 caracteres).")
    email: EmailStr = Field(..., description="Correo electrónico del usuario.")
    role: UserRole = Field(..., description="Rol del usuario: admin, support o user.")
    is_active: bool = Field(..., description="Indica si el usuario está activo en el sistema.")


class UserUpdate(BaseModel):
    """
    Modelo de ENTRADA para PATCH /users/{user_id}: actualización PARCIAL.

    Todos los campos son opcionales (valor por defecto None) porque
    el cliente solo envía los campos que realmente quiere cambiar;
    los que no envía se dejan intactos.
    """

    name: Optional[str] = Field(default=None, min_length=3, description="Nuevo nombre (opcional).")
    email: Optional[EmailStr] = Field(default=None, description="Nuevo correo (opcional).")
    role: Optional[UserRole] = Field(default=None, description="Nuevo rol (opcional).")
    is_active: Optional[bool] = Field(default=None, description="Nuevo estado activo (opcional).")


class UserResponse(UserBase):
    """
    Modelo de SALIDA (response_model) usado en todos los endpoints
    que devuelven usuarios. FastAPI filtra automáticamente cualquier
    campo interno (como 'notes' en UserInDB) que no esté declarado
    aquí, aunque sí exista en los datos guardados.
    """

    id: int = Field(..., description="Identificador único del usuario, asignado por el servidor.", examples=[1])


class UserInDB(UserResponse):
    """Cómo se guarda un usuario internamente. 'notes' nunca se expone al cliente."""

    notes: str = Field(default="", description="Nota interna de auditoría (no se expone en la API).")
