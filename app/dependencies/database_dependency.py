"""
app/dependencies/database_dependency.py
--------------------------------------------------------------
Dependencia reutilizable que entrega una sesión de base de datos a
cada endpoint que la necesite, garantizando que se cierre siempre al
terminar la petición (incluso si ocurre un error dentro de la ruta).
"""

from app.database.connection import SessionLocal


def get_db():
    """
    Dependencia de FastAPI: crea una sesión nueva por petición, la
    entrega con 'yield' (el código de la ruta se ejecuta en ese punto),
    y la cierra en el 'finally' pase lo que pase.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
