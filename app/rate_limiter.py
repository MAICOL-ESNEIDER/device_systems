"""
app/rate_limiter.py
--------------------------------------------------------------
Instancia compartida de Limiter (slowapi). Vive en su propio módulo
para que tanto main.py (donde se registra en la app) como los
archivos de rutas (donde se usa el decorador @limiter.limit(...))
puedan importarla sin crear una dependencia circular entre ellos.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

# get_remote_address identifica al cliente por su IP: cada IP tiene
# su propio contador de peticiones, independiente de las demás.
limiter = Limiter(key_func=get_remote_address)
