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

from app.dependencies.user_dependencies import get_user_or_404, validar_patch_no_vacio, verificar_api_key
from app.schemas.user_schema import UserCreate, UserReplace, UserResponse, UserRole, UserUpdate
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


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Actualizar un usuario por completo",
    description=(
        "Reemplaza TODOS los campos de un usuario existente (name, email, "
        "role, is_active). Responde 404 si el usuario no existe, y 400 si "
        "el nuevo correo ya pertenece a otro usuario."
    ),
    response_description="El usuario ya actualizado con los nuevos datos.",
)
def reemplazar_usuario(
    datos: UserReplace,
    usuario_actual: dict = Depends(get_user_or_404),
):
    """
    PUT /users/{user_id}

    A diferencia de PATCH, aquí el cliente debe enviar los 4 campos
    (UserReplace los exige todos como obligatorios): la filosofía de
    PUT es "reemplazar el recurso completo", no "tocar un pedacito".
    """
    correo_en_uso = user_service.obtener_usuario_por_email(datos.email, excluir_id=usuario_actual["id"])
    if correo_en_uso is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe otro usuario registrado con el correo '{datos.email}'",
        )
    return user_service.reemplazar_usuario(usuario_actual["id"], datos)


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="Actualizar un usuario parcialmente",
    description=(
        "Modifica SOLO los campos enviados en el body (ej: {\"role\": \"support\"}). "
        "Responde 400 si no se envía ningún campo, y 404 si el usuario no existe."
    ),
    response_description="El usuario con los campos ya actualizados.",
)
def actualizar_usuario_parcial(
    datos: UserUpdate = Depends(validar_patch_no_vacio),
    usuario_actual: dict = Depends(get_user_or_404),
):
    """
    PATCH /users/{user_id}

    'datos' ya pasó por la dependencia validar_patch_no_vacio, así
    que aquí es seguro asumir que al menos un campo viene con valor.
    Solo falta revisar el caso particular de que el nuevo correo (si
    se envió) no choque con el de otro usuario.
    """
    if datos.email is not None:
        correo_en_uso = user_service.obtener_usuario_por_email(datos.email, excluir_id=usuario_actual["id"])
        if correo_en_uso is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe otro usuario registrado con el correo '{datos.email}'",
            )
    return user_service.actualizar_usuario_parcial(usuario_actual["id"], datos)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un usuario",
    description=(
        "Elimina un usuario existente. Requiere la cabecera 'X-API-Key' "
        "para autorizar la operación (simulación de autenticación básica). "
        "Responde 404 si el usuario no existe, y 401 si falta o es "
        "incorrecta la cabecera de autorización."
    ),
    response_description="Sin contenido: el usuario fue eliminado correctamente.",
)
def eliminar_usuario(
    usuario_actual: dict = Depends(get_user_or_404),
    _autorizado: None = Depends(verificar_api_key),
) -> None:
    """
    DELETE /users/{user_id}

    Devuelve 204 No Content (sin cuerpo de respuesta) tras eliminar
    exitosamente. Combina DOS dependencias: primero confirma que el
    usuario existe, luego valida la cabecera de autorización.
    """
    user_service.eliminar_usuario(usuario_actual["id"])
    return None
