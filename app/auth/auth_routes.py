"""
app/auth/auth_routes.py
--------------------------------------------------------------
Endpoints de autenticación: registro, login (OAuth2 + JWT) y
consulta del usuario autenticado.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.auth.auth_service import autenticar_usuario, registrar_usuario
from app.auth.security import create_access_token
from app.dependencies.auth_dependency import get_current_active_user
from app.dependencies.database_dependency import get_db
from app.rate_limiter import limiter
from app.models.user_model import User
from app.schemas.auth_schema import Token, UserRegister
from app.schemas.user_schema import UserResponse
from app.services.user_service import obtener_usuario_por_email

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un nuevo usuario con contraseña segura",
    description=(
        "Crea un usuario validando nombre, email único, contraseña segura "
        "(mínimo 8 caracteres, mayúscula, minúscula, número, sin espacios) y rol permitido. "
        "La contraseña se guarda únicamente como hash bcrypt, nunca en texto plano."
    ),
    response_description="El usuario creado (sin la contraseña ni su hash).",
)
@limiter.limit("3/minute")
def register(request: Request, datos: UserRegister, db: Session = Depends(get_db)):
    if obtener_usuario_por_email(db, datos.email) is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe un usuario registrado con el correo '{datos.email}'",
        )
    return registrar_usuario(db, datos)


@router.post(
    "/login",
    response_model=Token,
    summary="Iniciar sesión y obtener un token JWT",
    description="Autentica al usuario con email y contraseña, y devuelve un token de acceso Bearer.",
    response_description="El token de acceso JWT.",
)
@limiter.limit("5/minute")
def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # OAuth2PasswordRequestForm usa 'username' por estándar, aunque
    # aquí ese campo se usa para recibir el correo electrónico.
    usuario = autenticar_usuario(db, email=form_data.username, password=form_data.password)
    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": usuario.email})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Consultar el usuario autenticado",
    description="Devuelve los datos del usuario dueño del token enviado en la cabecera Authorization.",
    response_description="Los datos del usuario autenticado (sin la contraseña).",
)
def read_current_user(current_user: User = Depends(get_current_active_user)):
    return current_user
