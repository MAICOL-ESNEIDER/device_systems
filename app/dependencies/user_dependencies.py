"""
app/dependencies/user_dependencies.py
--------------------------------------------------------------
Dependencias reutilizables inyectadas con Depends(). A partir de
EV09, get_user_or_404 consulta la base de datos real (antes
consultaba una lista en memoria).
"""

from typing import Optional

from fastapi import Depends, Header, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.dependencies.database_dependency import get_db
from app.schemas.user_schema import UserPatch
from app.services import user_service

# Clave simulada para el ejemplo de "autenticación básica mediante
# cabecera" (heredado de EV08). En un proyecto real vendría de una
# variable de entorno y usaría un mecanismo real de autenticación.
API_KEY_SIMULADA = "device-systems-secret-key"


def get_user_or_404(
    user_id: int = Path(..., description="ID del usuario", ge=1),
    db: Session = Depends(get_db),
):
    """Busca un usuario en la base de datos por su ID; lanza 404 si no existe."""
    usuario = user_service.obtener_usuario_por_id(db, user_id)
    if usuario is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    return usuario


def validar_patch_no_vacio(datos: UserPatch) -> UserPatch:
    """Rechaza (400) un PATCH que no envía absolutamente ningún campo."""
    sin_cambios = all(valor is None for valor in datos.model_dump().values())
    if sin_cambios:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Debes enviar al menos un campo para actualizar")
    return datos


def verificar_api_key(x_api_key: Optional[str] = Header(default=None)) -> None:
    """Simula autenticación básica leyendo la cabecera X-API-Key."""
    if x_api_key != API_KEY_SIMULADA:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Cabecera X-API-Key ausente o inválida")


def obtener_configuracion_api() -> dict:
    """Dependencia sin parámetros: expone la configuración general de la API."""
    return {"app_name": "device_systems", "version": "3.0.0"}
