"""
app/dependencies/auth_dependency.py
--------------------------------------------------------------
Dependencias reutilizables para proteger rutas: identificar al
usuario autenticado a partir de su token JWT, confirmar que esté
activo, y restringir operaciones según su rol.
"""

from typing import Callable, List

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.auth.security import decode_access_token
from app.dependencies.database_dependency import get_db
from app.models.user_model import User
from app.services.user_service import obtener_usuario_por_email

# 'tokenUrl' le dice a Swagger UI dónde está el endpoint de login,
# para que el botón "Authorize" sepa a dónde mandar las credenciales.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Decodifica el token JWT enviado en la cabecera
    'Authorization: Bearer <token>', y devuelve el usuario
    correspondiente. 401 si el token es inválido/expiró, o si el
    usuario del token ya no existe.
    """
    credenciales_invalidas = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if payload is None:
        raise credenciales_invalidas

    email: str = payload.get("sub")
    if email is None:
        raise credenciales_invalidas

    usuario = obtener_usuario_por_email(db, email)
    if usuario is None:
        raise credenciales_invalidas

    return usuario


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Igual que get_current_user, pero además exige que el usuario esté activo."""
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="El usuario está inactivo")
    return current_user


def require_roles(roles_permitidos: List[str]) -> Callable:
    """
    Fábrica de dependencias: genera una dependencia que exige que el
    usuario autenticado tenga uno de los roles indicados. Se usa así:
        Depends(require_roles(["admin", "support"]))
    En vez de escribir una función distinta por cada combinación de
    roles, esta única fábrica cubre cualquier combinación.
    """

    def verificar_rol(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in roles_permitidos:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Esta operación requiere uno de estos roles: {', '.join(roles_permitidos)}",
            )
        return current_user

    return verificar_rol


# Atajo para el caso más restrictivo (solo admin), pedido explícitamente por la guía.
require_admin = require_roles(["admin"])
