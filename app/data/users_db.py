"""
app/data/users_db.py
--------------------------------------------------------------
Simulación de base de datos en memoria para el recurso 'users'.
Es la ÚNICA fuente de verdad de los datos de usuarios en todo el
proyecto: app/services/user_service.py es quien la consulta y
modifica; las rutas nunca acceden a esta lista directamente.
"""

from app.schemas.user_schema import UserRole

# Lista de usuarios "guardados". Se reinicia cada vez que se
# reinicia el servidor (no hay persistencia real en disco), lo cual
# es suficiente para el alcance de este reto académico.
usuarios_db: list[dict] = [
    {"id": 1, "name": "Camila Restrepo", "email": "camila@ejemplo.com", "role": UserRole.admin, "is_active": True, "notes": "Usuario semilla"},
    {"id": 2, "name": "Andrés Gómez", "email": "andres@ejemplo.com", "role": UserRole.support, "is_active": True, "notes": "Usuario semilla"},
    {"id": 3, "name": "Laura Pérez", "email": "laura@ejemplo.com", "role": UserRole.user, "is_active": False, "notes": "Usuario semilla"},
    {"id": 4, "name": "Pedro Sánchez", "email": "pedro@ejemplo.com", "role": UserRole.user, "is_active": True, "notes": "Usuario semilla"},
]

# Contador interno para asignar IDs únicos a los usuarios nuevos.
_siguiente_id = 5


def obtener_siguiente_id() -> int:
    """Devuelve el siguiente ID disponible y avanza el contador interno."""
    global _siguiente_id
    id_asignado = _siguiente_id
    _siguiente_id += 1
    return id_asignado
