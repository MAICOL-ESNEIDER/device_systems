"""
app/routes/user_routes.py
--------------------------------------------------------------
Endpoints REST para el recurso 'users'. Los datos se guardan en una
lista en memoria (_usuarios_db) que simula una base de datos para
efectos de este ejercicio académico: se reinicia cada vez que se
reinicia el servidor, lo cual es suficiente para el alcance del reto.
"""

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Path, Query, status

from app.schemas.user_schema import UserResponse, UserRole

# El prefijo hace que TODAS las rutas de este router empiecen con
# /users. 'tags' agrupa estos endpoints bajo "users" en Swagger UI.
router = APIRouter(prefix="/users", tags=["users"])

# --- "Base de datos" en memoria ---
# Se guardan 4 usuarios de ejemplo (semilla) para poder probar los
# endpoints GET inmediatamente al levantar el servidor, sin tener
# que registrar usuarios manualmente primero.
_usuarios_db: List[dict] = [
    {
        "id": 1,
        "name": "Camila Restrepo",
        "email": "camila@ejemplo.com",
        "role": UserRole.admin,
        "is_active": True,
        "notes": "Usuario semilla",
    },
    {
        "id": 2,
        "name": "Andrés Gómez",
        "email": "andres@ejemplo.com",
        "role": UserRole.support,
        "is_active": True,
        "notes": "Usuario semilla",
    },
    {
        "id": 3,
        "name": "Laura Pérez",
        "email": "laura@ejemplo.com",
        "role": UserRole.user,
        "is_active": False,
        "notes": "Usuario semilla",
    },
    {
        "id": 4,
        "name": "Pedro Sánchez",
        "email": "pedro@ejemplo.com",
        "role": UserRole.user,
        "is_active": True,
        "notes": "Usuario semilla",
    },
]

# Contador simple para asignar IDs únicos a los usuarios que se
# registren más adelante (ver POST /users en la siguiente rama).
_siguiente_id = 5


@router.get(
    "/",
    response_model=List[UserResponse],
    summary="Listar usuarios (con filtros opcionales)",
)
def listar_usuarios(
    role: Optional[UserRole] = Query(
        default=None,
        description="Filtra los usuarios por rol: admin, support o user.",
    ),
    is_active: Optional[bool] = Query(
        default=None,
        description="Filtra los usuarios por estado activo (true) o inactivo (false).",
    ),
):
    """
    GET /users

    Devuelve la lista completa de usuarios. Si se envían los query
    parameters 'role' y/o 'is_active', la lista se filtra en
    consecuencia. Ejemplos:
    - GET /users              -> todos los usuarios
    - GET /users?role=admin   -> solo administradores
    - GET /users?is_active=true -> solo usuarios activos
    - GET /users?role=user&is_active=false -> ambos filtros combinados
    """
    resultado = _usuarios_db

    # Cada filtro es opcional e independiente: si no se envía ese
    # query parameter, su valor por defecto es None y no se aplica.
    if role is not None:
        resultado = [usuario for usuario in resultado if usuario["role"] == role]

    if is_active is not None:
        resultado = [usuario for usuario in resultado if usuario["is_active"] == is_active]

    return resultado


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Consultar un usuario por su ID",
)
def obtener_usuario(
    user_id: int = Path(
        ...,
        description="ID numérico del usuario a consultar.",
        ge=1,  # FastAPI valida automáticamente que sea >= 1 (responde 422 si no)
        examples=[1],
    )
):
    """
    GET /users/{user_id}

    Busca un usuario por su ID, recibido como path parameter. Si no
    existe ningún usuario con ese ID, responde con un error 404 y un
    mensaje claro en vez de dejar que el programa falle.
    """
    usuario = next((u for u in _usuarios_db if u["id"] == user_id), None)

    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró ningún usuario con id {user_id}.",
        )

    return usuario
