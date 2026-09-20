"""
app/routes/user_routes.py
--------------------------------------------------------------
Endpoints REST del recurso 'users', persistidos en base de datos
real mediante SQLAlchemy (sesión inyectada con Depends(get_db)).

A partir de EV11, consultar usuarios requiere estar autenticado
(Depends(get_current_active_user)); ver la tabla de protección de
rutas en el README para el resto de los recursos.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.dependencies.auth_dependency import get_current_active_user
from app.dependencies.database_dependency import get_db
from app.dependencies.user_dependencies import get_user_or_404, validar_patch_no_vacio, verificar_api_key
from app.models.user_model import User
from app.rate_limiter import limiter
from app.schemas.loan_schema import LoanResponse
from app.schemas.user_schema import UserCreate, UserPatch, UserResponse, UserRole, UserUpdate
from app.services import loan_service, user_service

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/",
    response_model=List[UserResponse],
    summary="Listar usuarios",
    description="Lista usuarios desde la base de datos, con filtros opcionales por rol/estado y orden por nombre o fecha de creación. Requiere autenticación.",
    response_description="Lista de usuarios.",
)
@limiter.limit("30/minute")
def listar_usuarios(
    request: Request,
    role: Optional[UserRole] = Query(default=None, description="Filtra por rol: admin, support o user."),
    is_active: Optional[bool] = Query(default=None, description="Filtra por estado activo."),
    order_by: Optional[str] = Query(default=None, description="Ordena por 'name' o 'created_at'."),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_active_user),
):
    return user_service.listar_usuarios(db, role=role, is_active=is_active, order_by=order_by)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Consultar un usuario por su ID",
    description="Busca un usuario por ID en la base de datos. Requiere autenticación. Responde 404 si no existe.",
    response_description="El usuario encontrado.",
)
def obtener_usuario(
    usuario=Depends(get_user_or_404),
    _current_user: User = Depends(get_current_active_user),
):
    return usuario


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un nuevo usuario",
    description="Crea un usuario en la base de datos. Rechaza correos duplicados.",
    response_description="El usuario recién creado.",
)
def crear_usuario(usuario: UserCreate, db: Session = Depends(get_db)):
    if user_service.obtener_usuario_por_email(db, usuario.email) is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe un usuario registrado con el correo '{usuario.email}'",
        )
    return user_service.crear_usuario(db, usuario)


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Actualizar un usuario por completo",
    description="Reemplaza todos los campos de un usuario existente. 404 si no existe, 400 si el correo pertenece a otro usuario.",
    response_description="El usuario actualizado.",
)
def actualizar_usuario_completo(
    datos: UserUpdate,
    usuario_actual=Depends(get_user_or_404),
    db: Session = Depends(get_db),
):
    correo_en_uso = user_service.obtener_usuario_por_email(db, datos.email, excluir_id=usuario_actual.id)
    if correo_en_uso is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe otro usuario registrado con el correo '{datos.email}'",
        )
    return user_service.actualizar_usuario_completo(db, usuario_actual.id, datos)


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="Actualizar un usuario parcialmente",
    description="Modifica solo los campos enviados. 400 si no se envía ninguno, 404 si el usuario no existe.",
    response_description="El usuario actualizado.",
)
def actualizar_usuario_parcial(
    datos: UserPatch = Depends(validar_patch_no_vacio),
    usuario_actual=Depends(get_user_or_404),
    db: Session = Depends(get_db),
):
    if datos.email is not None:
        correo_en_uso = user_service.obtener_usuario_por_email(db, datos.email, excluir_id=usuario_actual.id)
        if correo_en_uso is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe otro usuario registrado con el correo '{datos.email}'",
            )
    return user_service.actualizar_usuario_parcial(db, usuario_actual.id, datos)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un usuario",
    description="Elimina un usuario de la base de datos. Requiere la cabecera X-API-Key. 404 si no existe.",
    response_description="Sin contenido.",
)
def eliminar_usuario(
    usuario_actual=Depends(get_user_or_404),
    _autorizado: None = Depends(verificar_api_key),
    db: Session = Depends(get_db),
) -> None:
    user_service.eliminar_usuario(db, usuario_actual.id)
    return None


@router.get(
    "/{user_id}/loans",
    response_model=List[LoanResponse],
    summary="Historial de préstamos de un usuario",
    description="Lista todos los préstamos (activos e históricos) asociados a un usuario. 404 si el usuario no existe.",
    response_description="Lista de préstamos del usuario.",
)
def historial_prestamos_usuario(
    usuario=Depends(get_user_or_404),
    db: Session = Depends(get_db),
):
    return loan_service.listar_prestamos_por_usuario(db, usuario.id)
