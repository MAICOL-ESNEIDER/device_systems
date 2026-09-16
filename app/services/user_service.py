"""
app/services/user_service.py
--------------------------------------------------------------
Lógica de negocio del recurso 'users', ahora sobre base de datos
real vía SQLAlchemy (antes, en EV07/EV08, era una lista en memoria).
Cada función recibe la sesión 'db' inyectada por la ruta mediante
Depends(get_db), y opera sobre la tabla 'users'.
"""

from typing import Optional

from sqlalchemy.orm import Session

from app.models.user_model import User
from app.schemas.user_schema import UserCreate, UserPatch, UserRole, UserUpdate


def listar_usuarios(
    db: Session,
    role: Optional[UserRole] = None,
    is_active: Optional[bool] = None,
    order_by: Optional[str] = None,
) -> list[User]:
    """Lista usuarios, con filtros opcionales por rol/estado y orden por nombre o fecha de creación."""
    query = db.query(User)

    if role is not None:
        query = query.filter(User.role == role.value)
    if is_active is not None:
        query = query.filter(User.is_active == is_active)

    if order_by == "name":
        query = query.order_by(User.name)
    elif order_by == "created_at":
        query = query.order_by(User.created_at)

    return query.all()


def obtener_usuario_por_id(db: Session, user_id: int) -> Optional[User]:
    """Busca un usuario por su ID. Devuelve None si no existe."""
    return db.query(User).filter(User.id == user_id).first()


def obtener_usuario_por_email(db: Session, email: str, excluir_id: Optional[int] = None) -> Optional[User]:
    """
    Busca un usuario por su correo. 'excluir_id' permite ignorar al
    propio usuario al validar duplicados durante una actualización.
    """
    query = db.query(User).filter(User.email == email)
    if excluir_id is not None:
        query = query.filter(User.id != excluir_id)
    return query.first()


def crear_usuario(db: Session, datos: UserCreate) -> User:
    """Crea y persiste un nuevo usuario en la base de datos."""
    nuevo_usuario = User(
        name=datos.name,
        email=datos.email,
        role=datos.role.value,
        is_active=datos.is_active,
    )
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)  # recarga el objeto con lo que asignó la BD (id, created_at)
    return nuevo_usuario


def actualizar_usuario_completo(db: Session, user_id: int, datos: UserUpdate) -> Optional[User]:
    """Reemplaza TODOS los campos editables de un usuario existente (usado por PUT)."""
    usuario = obtener_usuario_por_id(db, user_id)
    if usuario is None:
        return None
    usuario.name = datos.name
    usuario.email = datos.email
    usuario.role = datos.role.value
    usuario.is_active = datos.is_active
    db.commit()
    db.refresh(usuario)
    return usuario


def actualizar_usuario_parcial(db: Session, user_id: int, datos: UserPatch) -> Optional[User]:
    """Actualiza SOLO los campos con valor (no None) en 'datos' (usado por PATCH)."""
    usuario = obtener_usuario_por_id(db, user_id)
    if usuario is None:
        return None
    cambios = datos.model_dump(exclude_none=True)
    for campo, valor in cambios.items():
        # 'role' llega como UserRole (Enum); la columna espera el string.
        setattr(usuario, campo, valor.value if isinstance(valor, UserRole) else valor)
    db.commit()
    db.refresh(usuario)
    return usuario


def eliminar_usuario(db: Session, user_id: int) -> bool:
    """Elimina un usuario por ID. Devuelve True si lo eliminó, False si no existía."""
    usuario = obtener_usuario_por_id(db, user_id)
    if usuario is None:
        return False
    db.delete(usuario)
    db.commit()
    return True
