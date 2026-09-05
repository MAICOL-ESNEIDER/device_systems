"""
app/services/user_service.py
--------------------------------------------------------------
Lógica de negocio del recurso 'users': listar, buscar, crear,
actualizar (completa y parcialmente) y eliminar.

Esta capa NO sabe nada de HTTP: no lanza HTTPException ni conoce
status codes, solo trabaja con datos y devuelve None/False cuando
algo no se encuentra. Son las rutas (o las dependencias) quienes
deciden cómo traducir eso a una respuesta HTTP. Esta separación
permitiría, por ejemplo, reutilizar esta misma lógica en un script
de consola o una tarea programada, sin arrastrar código de FastAPI.
"""

from typing import Optional

from app.data.users_db import obtener_siguiente_id, usuarios_db
from app.schemas.user_schema import UserCreate, UserReplace, UserRole, UserUpdate


def listar_usuarios(role: Optional[UserRole] = None, is_active: Optional[bool] = None) -> list[dict]:
    """Devuelve los usuarios guardados, aplicando los filtros opcionales que se reciban."""
    resultado = usuarios_db
    if role is not None:
        resultado = [u for u in resultado if u["role"] == role]
    if is_active is not None:
        resultado = [u for u in resultado if u["is_active"] == is_active]
    return resultado


def obtener_usuario_por_id(user_id: int) -> Optional[dict]:
    """Busca un usuario por su ID. Devuelve None si no existe."""
    return next((u for u in usuarios_db if u["id"] == user_id), None)


def obtener_usuario_por_email(email: str, excluir_id: Optional[int] = None) -> Optional[dict]:
    """
    Busca un usuario por su correo. 'excluir_id' permite ignorar al
    propio usuario al validar duplicados durante una actualización
    (PUT/PATCH): así no se marca como "duplicado" su propio correo
    si el cliente lo reenvía sin cambios.
    """
    for usuario in usuarios_db:
        if usuario["email"] == email and usuario["id"] != excluir_id:
            return usuario
    return None


def crear_usuario(datos: UserCreate) -> dict:
    """Crea y guarda un nuevo usuario a partir de datos ya validados por Pydantic."""
    nuevo_usuario = datos.model_dump()
    nuevo_usuario["id"] = obtener_siguiente_id()
    nuevo_usuario["notes"] = "Usuario creado vía POST /users"
    usuarios_db.append(nuevo_usuario)
    return nuevo_usuario


def reemplazar_usuario(user_id: int, datos: UserReplace) -> Optional[dict]:
    """Reemplaza TODOS los campos editables de un usuario existente (usado por PUT)."""
    usuario = obtener_usuario_por_id(user_id)
    if usuario is None:
        return None
    usuario["name"] = datos.name
    usuario["email"] = datos.email
    usuario["role"] = datos.role
    usuario["is_active"] = datos.is_active
    return usuario


def actualizar_usuario_parcial(user_id: int, datos: UserUpdate) -> Optional[dict]:
    """Actualiza SOLO los campos que vienen con valor (no None) en 'datos' (usado por PATCH)."""
    usuario = obtener_usuario_por_id(user_id)
    if usuario is None:
        return None
    cambios = datos.model_dump(exclude_none=True)
    usuario.update(cambios)
    return usuario


def eliminar_usuario(user_id: int) -> bool:
    """Elimina un usuario por ID. Devuelve True si lo eliminó, False si no existía."""
    usuario = obtener_usuario_por_id(user_id)
    if usuario is None:
        return False
    usuarios_db.remove(usuario)
    return True
