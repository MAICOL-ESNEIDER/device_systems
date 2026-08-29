"""
app/main.py
--------------------------------------------------------------
Punto de entrada de la API REST 'device_systems'. Aquí se crea la
instancia principal de FastAPI. Los routers de cada recurso (como
'users') se registran aquí a medida que se van implementando.
"""

from fastapi import FastAPI

# --- Metadatos de la aplicación ---
# title, description y version aparecen automáticamente en la
# documentación interactiva de Swagger UI (http://localhost:8000/docs)
app = FastAPI(
    title="device_systems",
    description="API REST para la gestión de usuarios del sistema device_systems.",
    version="1.0.0",
)


@app.get("/", tags=["root"], summary="Endpoint raíz de bienvenida")
def read_root():
    """Endpoint simple para verificar que la API está corriendo correctamente."""
    return {
        "mensaje": "Bienvenido a la API de device_systems.",
        "documentacion": "/docs",
    }
