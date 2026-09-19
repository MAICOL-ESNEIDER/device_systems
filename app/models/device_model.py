"""
app/models/device_model.py
--------------------------------------------------------------
Modelo SQLAlchemy de la tabla 'devices'. Representa los equipos
tecnológicos disponibles para préstamo (laptop, tablet, proyector,
cámara, router, monitor, etc.).
"""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from app.database.connection import Base


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    serial_number = Column(String, unique=True, nullable=False, index=True)
    device_type = Column(String, nullable=False)
    brand = Column(String, nullable=True)
    is_available = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Un dispositivo puede aparecer en muchos préstamos históricos
    # (uno "activo" a la vez, pero muchos a lo largo del tiempo).
    loans = relationship("Loan", back_populates="device")
