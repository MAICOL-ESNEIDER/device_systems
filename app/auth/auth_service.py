"""
app/auth/auth_service.py
--------------------------------------------------------------
Lógica de negocio de autenticación: registrar un nuevo usuario con
contraseña hasheada, y verificar credenciales de login.
"""

from typing import Optional

from sqlalchemy.orm import Session

from app.auth.security import get_password_hash, verify_password
from app.models.user_model import User
from app.schemas.auth_schema import UserRegister
from app.services.user_service import obtener_usuario_por_email


def registrar_usuario(db: Session, datos: UserRegister) -> User:
    """
    Crea un nuevo usuario con la contraseña ya hasheada. Nunca se
    guarda datos.password (texto plano) en la base de datos — solo
    el resultado de get_password_hash().
    """
    nuevo_usuario = User(
        name=datos.name,
        email=datos.email,
        hashed_password=get_password_hash(datos.password),
        role=datos.role.value,
        is_active=True,
    )
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)
    return nuevo_usuario


def autenticar_usuario(db: Session, email: str, password: str) -> Optional[User]:
    """
    Verifica las credenciales de login. Devuelve el usuario si el
    correo existe y la contraseña coincide con el hash guardado;
    devuelve None en cualquier otro caso (usuario no existe O
    contraseña incorrecta) — no se distingue cuál de las dos falló,
    para no darle pistas a un atacante sobre qué correos existen.
    """
    usuario = obtener_usuario_por_email(db, email)
    if usuario is None:
        return None
    if not verify_password(password, usuario.hashed_password):
        return None
    return usuario
