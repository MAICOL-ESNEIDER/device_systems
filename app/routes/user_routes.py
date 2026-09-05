"""
app/routes/user_routes.py
--------------------------------------------------------------
Endpoints REST del recurso 'users' (versión reestructurada EV08).

Esta capa se encarga SOLO de: recibir la petición HTTP, delegar la
lógica a app/services/user_service.py, y traducir el resultado a la
respuesta HTTP correcta (status code + response_model). Ya no
guarda los datos aquí mismo (a diferencia de la versión EV07): esa
responsabilidad ahora vive en app/data y app/services.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies.user_dependencies import get_user_or_404
from app.schemas.user_schema import UserCreate, UserResponse, UserRole
from app.services import user_service

# El prefijo hace que TODAS las rutas de este router empiecen con
# /users. 'tags' agrupa estos endpoints bajo "Users" en Swagger UI.
router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/",
    response_model=List[UserResponse],
    summary="Listar usuarios",
    description="Devuelve todos los usuarios registrados, con filtros opcionales por rol y/o estado activo.",
    response_description="Lista de usuarios que cumplen los filtros indicados.",
)
def listar_usuarios(
    role: Optional[UserRole] = Query(default=None, description="Filtra por rol: admin, support o user."),
    is_active: Optional[bool] = Query(default=None, description="Filtra por estado activo (true) o inactivo (false)."),
):
    """GET /users — delega el listado y el filtrado a la capa de servicios."""
    return user_service.listar_usuarios(role=role, is_active=is_active)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Consultar un usuario por su ID",
    description="Busca un usuario por su ID (path parameter). Responde 404 si no existe.",
    response_description="El usuario encontrado.",
)
def obtener_usuario(usuario: dict = Depends(get_user_or_404)):
    """
    GET /users/{user_id}

    La búsqueda y el manejo del 404 ya no viven aquí: los hace la
    dependencia get_user_or_404, que además se reutilizará en PUT,
    PATCH y DELETE en la siguiente rama.
    """
    return usuario


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un nuevo usuario",
    description="Crea un usuario nuevo, validando los datos con Pydantic y rechazando correos duplicados.",
    response_description="El usuario recién creado, con su ID ya asignado.",
)
def crear_usuario(usuario: UserCreate):
    """POST /users"""
    if user_service.obtener_usuario_por_email(usuario.email) is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe un usuario registrado con el correo '{usuario.email}'",
        )
    return user_service.crear_usuario(usuario)
