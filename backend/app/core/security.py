"""
Security Core - JWT, Password Hashing, Token Management
"""
from datetime import datetime, timedelta
from typing import Any, Dict
from jose import JWTError, jwt
from passlib.context import CryptContext
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import secrets

from app.core.config import settings


# ==============================================
# Password Hashing con Argon2
# ==============================================
argon2_hasher = PasswordHasher(
    time_cost=2,  # Number of iterations
    memory_cost=65536,  # 64 MB
    parallelism=4,  # Number of parallel threads
    hash_len=32,  # Length of the hash in bytes
    salt_len=16  # Length of the salt in bytes
)

# Fallback context para compatibilidad (si migramos de bcrypt)
pwd_context = CryptContext(
    schemes=["argon2", "bcrypt"],
    deprecated="auto",
    argon2__time_cost=2,
    argon2__memory_cost=65536,
    argon2__parallelism=4,
)


def hash_password(password: str) -> str:
    """
    Hash password usando Argon2
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password
    """
    return argon2_hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verificar password contra hash
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password from database
        
    Returns:
        True si el password es válido
    """
    try:
        argon2_hasher.verify(hashed_password, plain_password)
        return True
    except VerifyMismatchError:
        # Fallback a bcrypt si el hash es viejo
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False


def check_password_needs_rehash(hashed_password: str) -> bool:
    """
    Verificar si un password hash necesita rehashing
    (útil para migrar de bcrypt a argon2)
    
    Args:
        hashed_password: Hashed password from database
        
    Returns:
        True si necesita rehash
    """
    return argon2_hasher.check_needs_rehash(hashed_password)


# ==============================================
# JWT Token Management
# ==============================================
def create_access_token(
    data: Dict[str, Any],
    expires_delta: timedelta | None = None
) -> str:
    """
    Crear JWT access token
    
    Args:
        data: Payload data (debe incluir 'sub' con user_id)
        expires_delta: Tiempo de expiración personalizado
        
    Returns:
        JWT token codificado
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(
    data: Dict[str, Any],
    expires_delta: timedelta | None = None
) -> str:
    """
    Crear JWT refresh token
    
    Args:
        data: Payload data (debe incluir 'sub' con user_id)
        expires_delta: Tiempo de expiración personalizado
        
    Returns:
        JWT refresh token codificado
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
    
    # Agregar jti (JWT ID) único para tracking/revocación
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh",
        "jti": secrets.token_urlsafe(32)
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any] | None:
    """
    Decodificar y validar JWT token
    
    Args:
        token: JWT token
        
    Returns:
        Payload dict o None si es inválido
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validar fortaleza de password según políticas
    
    Args:
        password: Plain text password
        
    Returns:
        Tuple (is_valid, error_message)
    """
    if len(password) < settings.PASSWORD_MIN_LENGTH:
        return False, f"Password debe tener al menos {settings.PASSWORD_MIN_LENGTH} caracteres"
    
    if settings.PASSWORD_REQUIRE_UPPERCASE and not any(c.isupper() for c in password):
        return False, "Password debe contener al menos una mayúscula"
    
    if settings.PASSWORD_REQUIRE_LOWERCASE and not any(c.islower() for c in password):
        return False, "Password debe contener al menos una minúscula"
    
    if settings.PASSWORD_REQUIRE_DIGIT and not any(c.isdigit() for c in password):
        return False, "Password debe contener al menos un número"
    
    if settings.PASSWORD_REQUIRE_SPECIAL:
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(c in special_chars for c in password):
            return False, "Password debe contener al menos un carácter especial"
    
    return True, ""


def generate_random_password(length: int = 16) -> str:
    """
    Generar password aleatorio seguro
    
    Args:
        length: Longitud del password
        
    Returns:
        Password generado
    """
    return secrets.token_urlsafe(length)
