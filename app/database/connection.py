"""
app/database/connection.py
--------------------------------------------------------------
Configuración de la conexión a la base de datos con SQLAlchemy.
Define el engine, la fábrica de sesiones (SessionLocal) y la clase
Base de la que heredan todos los modelos ORM del proyecto.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Base de datos SQLite para desarrollo. El archivo se crea
# automáticamente en la raíz del proyecto la primera vez que se usa.
DATABASE_URL = "sqlite:///./device_systems.db"

# 'check_same_thread=False' es necesario específicamente para SQLite:
# por defecto no permite que una conexión se use desde un hilo
# distinto al que la creó, pero FastAPI puede atender peticiones en
# hilos diferentes. No es necesario con otros motores (PostgreSQL, etc.).
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

# SessionLocal es una "fábrica" de sesiones: cada petición HTTP recibe
# su propia sesión (ver app/dependencies/database_dependency.py); una
# sesión nunca se comparte entre peticiones distintas.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base es la clase de la que heredan todos los modelos ORM
# (app/models/*.py). SQLAlchemy usa su metadata para saber qué tablas
# existen y poder crearlas (o, desde EV10, compararlas con Alembic).
Base = declarative_base()
