"""
app/auth/security.py
--------------------------------------------------------------
Funciones de seguridad: hash de contraseñas con passlib (bcrypt) y
creación/validación de tokens JWT con python-jose. Ninguna
contraseña se guarda ni se compara jamás en texto plano.
"""

import os
from datetime import datetime, timedelta
from typing import Optional

from dotenv import load_dotenv
from jose import JWTError, jwt
from passlib.context import CryptContext

load_dotenv()

# Se leen desde variables de entorno (.env) en vez de estar
# escritas en el código — ver .env.example para el formato esperado.
SECRET_KEY = os.getenv("SECRET_KEY", "clave-de-desarrollo-no-usar-en-produccion")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# CryptContext se encarga de generar y verificar hashes bcrypt,
# y de "actualizar" automáticamente hashes generados con esquemas
# antiguos si algún día se cambia el algoritmo (deprecated="auto").
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    """Genera el hash bcrypt de una contraseña en texto plano."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Compara una contraseña en texto plano contra su hash guardado."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Crea un token JWT firmado. 'data' normalmente incluye al menos
    {"sub": email_del_usuario}. 'exp' (expiración) se agrega siempre,
    para que el token deje de ser válido pasado cierto tiempo.
    """
    to_encode = data.copy()
    expira = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expira})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    """
    Decodifica y valida un token JWT. Devuelve el payload si es
    válido y no ha expirado; devuelve None si es inválido, fue
    alterado, o ya expiró (jose lanza JWTError en esos casos).
    """
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None
