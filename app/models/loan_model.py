"""
app/models/loan_model.py
--------------------------------------------------------------
Modelo SQLAlchemy de la tabla 'loans'. Representa el préstamo de un
dispositivo a un usuario: es la tabla "puente" que relaciona User y
Device mediante claves foráneas (ForeignKey).
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database.connection import Base


class Loan(Base):
    __tablename__ = "loans"

    id = Column(Integer, primary_key=True, index=True)

    # ForeignKey: garantiza integridad referencial — un préstamo
    # SIEMPRE debe apuntar a un usuario y a un dispositivo que existan.
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)

    loan_date = Column(DateTime, default=datetime.utcnow)
    return_date = Column(DateTime, nullable=True)
    status = Column(String, nullable=False, default="active")  # active | returned | overdue

    # 'back_populates' conecta esta relación con el lado opuesto
    # declarado en User.loans y Device.loans, para que SQLAlchemy
    # mantenga ambos extremos sincronizados automáticamente.
    user = relationship("User", back_populates="loans")
    device = relationship("Device", back_populates="loans")
