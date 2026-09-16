"""
app/models/user_model.py
--------------------------------------------------------------
Modelo SQLAlchemy de la tabla 'users'. Representa la ESTRUCTURA DE
LA TABLA en la base de datos: columnas, tipos y restricciones.

No confundir con los schemas Pydantic (app/schemas/user_schema.py),
que definen el CONTRATO de entrada/salida de la API. Ver la
diferencia completa explicada en el README.
"""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String

from app.database.connection import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    role = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # NOTA: la relación con Loan ("un usuario puede tener muchos
    # préstamos") se agrega en EV10, cuando el modelo Loan exista.
