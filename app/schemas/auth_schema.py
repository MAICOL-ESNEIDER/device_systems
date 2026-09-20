"""
app/schemas/auth_schema.py
--------------------------------------------------------------
Schemas Pydantic v2 para autenticación: registro, login y el token
JWT de respuesta. Usa field_validator para aplicar las reglas de
seguridad de la contraseña (Fase 6 de la guía).
"""

import re
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.schemas.user_schema import UserRole


class UserRegister(BaseModel):
    """Entrada para POST /auth/register."""

    name: str = Field(..., min_length=3, description="Nombre completo del usuario.")
    email: EmailStr = Field(..., description="Correo electrónico único.")
    password: str = Field(..., min_length=8, description="Contraseña (ver reglas de seguridad).")
    role: UserRole = Field(default=UserRole.user, description="Rol del usuario: admin, support o user.")

    @field_validator("password")
    @classmethod
    def validar_seguridad_password(cls, valor: str) -> str:
        """
        Reglas mínimas de la guía: al menos 8 caracteres, una
        mayúscula, una minúscula, un número, y sin espacios en blanco.
        Se valida aquí (no solo con min_length) porque son reglas de
        *contenido*, no solo de longitud.
        """
        if " " in valor:
            raise ValueError("La contraseña no puede contener espacios en blanco.")
        if not re.search(r"[A-Z]", valor):
            raise ValueError("La contraseña debe tener al menos una letra mayúscula.")
        if not re.search(r"[a-z]", valor):
            raise ValueError("La contraseña debe tener al menos una letra minúscula.")
        if not re.search(r"\d", valor):
            raise ValueError("La contraseña debe tener al menos un número.")
        return valor


class UserLogin(BaseModel):
    """Entrada para POST /auth/login (además de OAuth2PasswordRequestForm, ver auth_routes.py)."""

    email: EmailStr
    password: str


class Token(BaseModel):
    """Salida de POST /auth/login."""

    model_config = ConfigDict(from_attributes=True)

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """
    Representa el contenido (payload) decodificado de un token JWT
    válido. Se usa internamente en las dependencias de autenticación
    (app/dependencies/auth_dependency.py), no se expone en la API.
    """

    email: Optional[str] = None
