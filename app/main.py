"""
app/main.py
--------------------------------------------------------------
Punto de entrada de la API REST 'device_systems' (v2.0.0). Crea la
instancia de FastAPI con metadatos completos para Swagger/OpenAPI,
registra el router de usuarios, y agrega un middleware con cabeceras
HTTP personalizadas en todas las respuestas.
"""

from fastapi import Depends, FastAPI, Request

from app.dependencies.user_dependencies import obtener_configuracion_api
from app.routes.user_routes import router as user_router

# --- Metadatos de la aplicación ---
# Aparecen automáticamente en Swagger UI (/docs) y ReDoc (/redoc):
# título, descripción, versión y datos de contacto del autor.
app = FastAPI(
    title="device_systems API",
    description=(
        "API REST para la gestión de usuarios del sistema device_systems. "
        "Incluye CRUD completo del recurso 'users' (crear, listar, consultar, "
        "actualizar total y parcialmente, y eliminar), validaciones con "
        "Pydantic v2, manejo de errores con HTTPException, códigos de estado "
        "HTTP apropiados por operación, e inyección de dependencias reutilizables "
        "con Depends()."
    ),
    version="2.0.0",
    contact={
        "name": "Maicol Esneider",
        "url": "https://github.com/MAICOL-ESNEIDER",
    },
)

# Registrar el router de usuarios: todas sus rutas quedan bajo /users
# (prefijo y tags="Users" ya definidos dentro del propio router).
app.include_router(user_router)


@app.middleware("http")
async def agregar_cabeceras_personalizadas(request: Request, call_next):
    """
    Middleware HTTP que se ejecuta en TODAS las peticiones a la API.
    Añade dos cabeceras personalizadas a cada respuesta: el nombre de
    la app y la versión actual, útil para que cualquier cliente sepa
    con certeza qué versión de la API está consumiendo.
    """
    response = await call_next(request)
    response.headers["X-App-Name"] = "device_systems"
    response.headers["X-API-Version"] = "2.0"
    return response


@app.get(
    "/",
    tags=["Root"],
    summary="Endpoint raíz de bienvenida",
    description="Verifica que la API está corriendo y expone su configuración general (vía Depends).",
    response_description="Mensaje de bienvenida y enlace a la documentación interactiva.",
)
def read_root(config: dict = Depends(obtener_configuracion_api)):
    """
    Endpoint simple para comprobar que el servidor responde. Usa
    obtener_configuracion_api como dependencia para demostrar que
    Depends() también sirve para funciones sin parámetros de la
    petición, no solo para validaciones de path/body/header.
    """
    return {
        "mensaje": f"Bienvenido a la API de {config['app_name']} (v{config['version']}).",
        "documentacion": "/docs",
    }
