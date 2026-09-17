"""
app/main.py
--------------------------------------------------------------
Punto de entrada de device_systems (v3.0.0 — EV10: relaciones,
migraciones con Alembic y consultas con joins). Registra los 3
routers (users, devices, loans) y agrega cabeceras personalizadas
a todas las respuestas mediante middleware.
"""

from fastapi import Depends, FastAPI, Request

from app.database.connection import Base, engine
from app.dependencies.user_dependencies import obtener_configuracion_api
from app.routes.device_routes import router as device_router
from app.routes.loan_routes import router as loan_router
from app.routes.user_routes import router as user_router

# Crea todas las tablas declaradas en los modelos si todavía no
# existen. Se conserva por ahora durante el desarrollo de EV10; se
# retira más adelante en esta misma rama cuando Alembic queda
# configurado como la única fuente de verdad del esquema.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="device_systems API",
    description=(
        "API REST para la gestión de usuarios, dispositivos y préstamos de "
        "device_systems. Incluye persistencia con SQLAlchemy, migraciones "
        "con Alembic, relaciones entre modelos y consultas con joins."
    ),
    version="3.0.0",
    contact={"name": "Maicol Esneider", "url": "https://github.com/MAICOL-ESNEIDER"},
)

app.include_router(user_router)
app.include_router(device_router)
app.include_router(loan_router)


@app.middleware("http")
async def agregar_cabeceras_personalizadas(request: Request, call_next):
    """Middleware que añade X-App-Name y X-API-Version a toda respuesta."""
    response = await call_next(request)
    response.headers["X-App-Name"] = "device_systems"
    response.headers["X-API-Version"] = "3.0"
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
