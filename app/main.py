"""
app/main.py
--------------------------------------------------------------
Punto de entrada de device_systems (v2.1.0 — EV09: persistencia con
SQLAlchemy). Crea las tablas en la base de datos al iniciar si no
existen. A partir de EV10 esta responsabilidad pasa a Alembic.
"""

from fastapi import Depends, FastAPI, Request

from app.database.connection import Base, engine
from app.dependencies.user_dependencies import obtener_configuracion_api
from app.routes.user_routes import router as user_router

# Crea todas las tablas declaradas en los modelos (app/models/*.py)
# si todavía no existen en la base de datos.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="device_systems API",
    description=(
        "API REST para la gestión de usuarios de device_systems, con "
        "persistencia real en base de datos vía SQLAlchemy."
    ),
    version="2.1.0",
    contact={"name": "Maicol Esneider", "url": "https://github.com/MAICOL-ESNEIDER"},
)

app.include_router(user_router)


@app.middleware("http")
async def agregar_cabeceras_personalizadas(request: Request, call_next):
    """Middleware que añade X-App-Name y X-API-Version a toda respuesta."""
    response = await call_next(request)
    response.headers["X-App-Name"] = "device_systems"
    response.headers["X-API-Version"] = "2.1"
    return response


@app.get(
    "/",
    tags=["Root"],
    summary="Endpoint raíz de bienvenida",
    description="Verifica que la API está corriendo y expone su configuración general.",
)
def read_root(config: dict = Depends(obtener_configuracion_api)):
    return {
        "mensaje": f"Bienvenido a la API de {config['app_name']} (v{config['version']}).",
        "documentacion": "/docs",
    }
