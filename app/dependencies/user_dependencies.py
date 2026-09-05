"""
app/dependencies/user_dependencies.py
--------------------------------------------------------------
Funciones reutilizables inyectadas en los endpoints mediante
Depends(). Cada una encapsula una validación (o un dato) que varias
rutas necesitan, para no repetir la misma lógica en cada endpoint.
"""

from typing import Optional

from fastapi import Header, HTTPException, Path, status

from app.schemas.user_schema import UserUpdate
from app.services import user_service

# Clave simulada para el ejemplo de "autenticación básica mediante
# cabecera". En un proyecto real vendría de una variable de entorno
# y usaría un mecanismo real (JWT, OAuth2, API keys hasheadas, etc.)
# — aquí se simplifica a propósito para el alcance académico del reto.
API_KEY_SIMULADA = "device-systems-secret-key"


def get_user_or_404(user_id: int = Path(..., description="ID del usuario", ge=1)) -> dict:
    """
    Dependencia reutilizable: busca un usuario por su ID (path
    parameter) y, si no existe, lanza automáticamente un 404 con
    mensaje claro. Se usa en GET/PUT/PATCH/DELETE por ID, evitando
    repetir la búsqueda + el "if usuario is None" en cada endpoint.
    """
    usuario = user_service.obtener_usuario_por_id(user_id)
    if usuario is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    return usuario


def validar_patch_no_vacio(datos: UserUpdate) -> UserUpdate:
    """
    Dependencia reutilizable para PATCH: si el cliente no envió
    absolutamente ningún campo para actualizar, responde 400 en vez
    de aceptar un PATCH que no cambiaría nada.
    """
    sin_cambios = all(valor is None for valor in datos.model_dump().values())
    if sin_cambios:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debes enviar al menos un campo para actualizar",
        )
    return datos


def verificar_api_key(x_api_key: Optional[str] = Header(default=None)) -> None:
    """
    Dependencia reutilizable que simula una autenticación básica
    leyendo la cabecera personalizada 'X-API-Key'. Se usa en la
    operación más sensible del recurso (DELETE), para mostrar que
    Depends() también valida cabeceras, no solo body o path.
    """
    if x_api_key != API_KEY_SIMULADA:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Cabecera X-API-Key ausente o inválida",
        )


def obtener_configuracion_api() -> dict:
    """
    Dependencia reutilizable sin parámetros: expone la configuración
    general de la API. Demuestra que Depends() también funciona con
    funciones que no dependen directamente de la petición HTTP.
    """
    return {"app_name": "device_systems", "version": "2.0.0"}
