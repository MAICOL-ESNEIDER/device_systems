"""
app/main.py
--------------------------------------------------------------
Punto de entrada de device_systems (v4.0.0 — EV11: autenticación,
middleware, CORS, rate limiting y validación avanzada). Registra los
4 routers (auth, users, devices, loans), configura CORS, rate
limiting global, y el middleware personalizado de trazabilidad.
"""

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.auth.auth_routes import router as auth_router
from app.dependencies.user_dependencies import obtener_configuracion_api
from app.middlewares.request_middleware import RequestContextMiddleware
from app.rate_limiter import limiter
from app.routes.device_routes import router as device_router
from app.routes.loan_routes import router as loan_router
from app.routes.user_routes import router as user_router

app = FastAPI(
    title="device_systems API",
    description=(
        "API REST segura para gestión de usuarios, dispositivos y préstamos. "
        "Incluye autenticación OAuth2 + JWT, hash de contraseñas con passlib, "
        "protección de rutas por rol, middleware personalizado, CORS y rate limiting."
    ),
    version="4.0.0",
    contact={"name": "Maicol Esneider", "url": "https://github.com/MAICOL-ESNEIDER"},
)

# --- Rate limiting (slowapi) ---
# Se registra el limiter en el estado de la app y el manejador que
# convierte un límite excedido en una respuesta 429 Too Many Requests.
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# --- CORS ---
# Solo se permiten estos dos orígenes de desarrollo (front-end local).
# allow_credentials=True + allow_origins=["*"] está PROHIBIDO por la
# especificación CORS (el navegador lo rechaza) y sería peligroso si
# funcionara: permitiría que cualquier sitio web hiciera peticiones
# autenticadas a esta API usando las credenciales del usuario. Por
# eso aquí se listan orígenes explícitos en vez de usar "*".
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Middleware personalizado ---
# Cabeceras de trazabilidad (X-App-Name, X-Process-Time, X-Request-ID)
# y registro de cada petición. Ver app/middlewares/request_middleware.py.
app.add_middleware(RequestContextMiddleware)

# --- Routers ---
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(device_router)
app.include_router(loan_router)


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
