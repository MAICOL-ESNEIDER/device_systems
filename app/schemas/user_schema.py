"""
app/schemas/user_schema.py
--------------------------------------------------------------
Modelos Pydantic para validar los datos de usuario que entran y
salen de la API. Separar el modelo de entrada (UserCreate) del de
salida (UserResponse) permite controlar exactamente qué datos se le
piden al cliente y qué datos se le devuelven, sin mezclar ambas
responsabilidades en una sola clase.
"""

from enum import Enum

from pydantic import BaseModel, EmailStr, Field


class UserRole(str, Enum):
    """
    Roles permitidos para un usuario del sistema.

    Heredar de (str, Enum) tiene dos ventajas: FastAPI valida
    automáticamente que el valor recibido sea una de estas tres
    opciones (y responde 422 si no lo es), y además el valor se
    muestra como texto simple en la documentación de Swagger, en vez
    de un objeto Enum poco legible.
    """

    admin = "admin"
    support = "support"
    user = "user"


class UserBase(BaseModel):
    """
    Campos que comparten tanto la creación como la respuesta de un
    usuario. Se definen una sola vez aquí y las demás clases heredan
    de esta, evitando repetir las mismas validaciones dos veces.
    """

    name: str = Field(
        ...,
        min_length=3,
        description="Nombre completo del usuario (mínimo 3 caracteres).",
        examples=["Camila Restrepo"],
    )
    email: EmailStr = Field(
        ...,
        description="Correo electrónico del usuario. Debe tener un formato válido.",
        examples=["camila@ejemplo.com"],
    )
    role: UserRole = Field(
        ...,
        description="Rol del usuario dentro del sistema: admin, support o user.",
        examples=["user"],
    )
    is_active: bool = Field(
        default=True,
        description="Indica si el usuario está activo en el sistema.",
    )


class UserCreate(UserBase):
    """
    Modelo de ENTRADA usado en el endpoint POST /users.

    No incluye 'id' a propósito: ese valor lo asigna el servidor
    automáticamente al registrar el usuario, no lo decide quien hace
    la petición.
    """

    pass


class UserResponse(UserBase):
    """
    Modelo de SALIDA (response_model) usado en todos los endpoints
    que devuelven usuarios (GET y POST).

    Incluye 'id' porque el cliente sí necesita conocerlo una vez el
    usuario existe. Al declararse como response_model en las rutas,
    FastAPI filtra automáticamente cualquier campo interno que exista
    en los datos guardados pero que NO esté declarado en esta clase
    (por ejemplo, 'notes' en UserInDB) — así se evita exponer
    información interna que el cliente no necesita ver.
    """

    id: int = Field(
        ...,
        description="Identificador único del usuario, asignado por el servidor.",
        examples=[1],
    )


class UserInDB(UserResponse):
    """
    Representa cómo se guarda un usuario internamente en la
    'base de datos' en memoria de este proyecto.

    Incluye un campo adicional, 'notes', que es información interna
    de auditoría. Este campo NUNCA se expone al cliente porque los
    endpoints usan UserResponse (no UserInDB) como response_model.
    """

    notes: str = Field(
        default="",
        description="Nota interna de auditoría, de uso exclusivo del sistema (no se expone en la API).",
    )
