"""
app/main.py
--------------------------------------------------------------
Punto de entrada de la API REST 'device_systems'. Aquí se crea la
instancia principal de FastAPI. Los routers de cada recurso (como
'users') se registran aquí a medida que se van implementando.
"""

from fastapi import FastAPI, Request

from app.routes.user_routes import router as user_router

# --- Metadatos de la aplicación ---
# title, description y version aparecen automáticamente en la
# documentación interactiva de Swagger UI (http://localhost:8000/docs)
app = FastAPI(
    title="device_systems",
    description="API REST para la gestión de usuarios del sistema device_systems.",
    version="1.0.0",
)

# Registrar el router de usuarios: todas sus rutas quedan disponibles
# bajo el prefijo /users (definido dentro del propio router).
app.include_router(user_router)


@app.middleware("http")
async def agregar_cabeceras_personalizadas(request: Request, call_next):
    """
    Middleware HTTP que se ejecuta en TODAS las peticiones a la API,
    sin importar el endpoint. 'call_next' ejecuta la ruta
    correspondiente y devuelve su respuesta; aquí simplemente se le
    añaden dos cabeceras personalizadas antes de enviarla al cliente:

    - X-App-Name: identifica qué aplicación respondió la petición.
    - X-API-Version: permite al cliente saber qué versión de la API
      está consumiendo, útil si en el futuro hay cambios importantes.
    """
    response = await call_next(request)
    response.headers["X-App-Name"] = "device_systems"
    response.headers["X-API-Version"] = "1.0"
    return response


@app.get("/", tags=["root"], summary="Endpoint raíz de bienvenida")
def read_root():
    """Endpoint simple para verificar que la API está corriendo correctamente."""
    return {
        "mensaje": "Bienvenido a la API de device_systems.",
        "documentacion": "/docs",
    }
