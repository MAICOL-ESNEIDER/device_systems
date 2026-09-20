"""
app/middlewares/request_middleware.py
--------------------------------------------------------------
Middleware personalizado que se ejecuta en TODA petición a la API:
mide el tiempo de respuesta, propaga o genera un ID de correlación
por petición, agrega cabeceras informativas, y deja un registro
(log) de cada petición atendida.
"""

import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class RequestContextMiddleware(BaseHTTPMiddleware):
    """
    Se implementa como una clase (BaseHTTPMiddleware) en vez de la
    forma decorador (@app.middleware("http")) usada en versiones
    anteriores, porque así queda en su propio archivo reutilizable
    y es más fácil de leer cuando hace varias cosas a la vez.
    """

    async def dispatch(self, request: Request, call_next):
        # Si el cliente ya envió un X-Request-ID (por ejemplo, para
        # rastrear la petición a través de varios servicios), se
        # reutiliza; si no, se genera uno nuevo aquí.
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        inicio = time.perf_counter()
        response = await call_next(request)
        duracion = time.perf_counter() - inicio

        response.headers["X-App-Name"] = "device_systems"
        response.headers["X-Process-Time"] = f"{duracion:.4f}"
        response.headers["X-Request-ID"] = request_id

        # Registro simple en consola: método, ruta, código de estado,
        # duración e ID de correlación de cada petición atendida.
        print(
            f"[{request_id}] {request.method} {request.url.path} "
            f"-> {response.status_code} ({duracion:.4f}s)"
        )

        return response
