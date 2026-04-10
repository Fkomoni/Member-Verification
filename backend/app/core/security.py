from datetime import datetime, timedelta, timezone

from cryptography.fernet import Fernet
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password[:72], hashed_password)


def hash_password(password: str) -> str:
    # bcrypt has a 72-byte limit — truncate if needed
    return pwd_context.hash(password[:72])


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None


def encrypt_biometric_template(template_bytes: bytes) -> bytes:
    fernet = Fernet(settings.BIOMETRIC_ENCRYPTION_KEY.encode())
    return fernet.encrypt(template_bytes)


def decrypt_biometric_template(encrypted_template: bytes) -> bytes:
    fernet = Fernet(settings.BIOMETRIC_ENCRYPTION_KEY.encode())
    return fernet.decrypt(encrypted_template)
