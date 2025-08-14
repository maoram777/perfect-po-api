from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from ..config import settings

# Support both argon2 and bcrypt for transition period
# argon2 is preferred, bcrypt is deprecated but still supported for existing users
pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated=["bcrypt"])


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def verify_and_upgrade_password(plain_password: str, hashed_password: str) -> tuple[bool, str]:
    """
    Verify a password and return (is_valid, new_hash).
    If the password is valid and uses bcrypt, returns a new argon2 hash.
    If the password is valid and uses argon2, returns the same hash.
    If the password is invalid, returns (False, "").
    """
    if pwd_context.verify(plain_password, hashed_password):
        # Check if the hash is using bcrypt (deprecated)
        if hashed_password.startswith('$2b$') or hashed_password.startswith('$2a$'):
            # Generate new argon2 hash for future use
            new_hash = pwd_context.hash(plain_password)
            return True, new_hash
        else:
            # Already using argon2, return the same hash
            return True, hashed_password
    else:
        return False, ""


def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt_expiration_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """Verify JWT token and return payload."""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError:
        return None

