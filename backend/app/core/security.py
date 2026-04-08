"""
Security utilities — JWT, password hashing, encryption, and data masking.
"""

import re
from datetime import datetime, timedelta, timezone

from cryptography.fernet import Fernet
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


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


# ── Data Masking ─────────────────────────────────────────────


def mask_account_number(account_number: str) -> str:
    """Mask account number: show first 2 and last 2 digits. e.g. 20****78"""
    if not account_number or len(account_number) < 4:
        return "****"
    return account_number[:2] + "*" * (len(account_number) - 4) + account_number[-2:]


def mask_phone(phone: str) -> str:
    """Mask phone: show first 4 and last 2 digits. e.g. 0801****78"""
    if not phone or len(phone) < 6:
        return "****"
    return phone[:4] + "*" * (len(phone) - 6) + phone[-2:]


# ── Input Sanitization ───────────────────────────────────────


def sanitize_text(text: str | None) -> str | None:
    """Strip leading/trailing whitespace and collapse internal whitespace."""
    if text is None:
        return None
    text = text.strip()
    # Remove null bytes
    text = text.replace("\x00", "")
    return text if text else None


def validate_enrollee_id_format(enrollee_id: str) -> bool:
    """Validate enrollee ID format (alphanumeric + hyphens)."""
    return bool(re.match(r"^[A-Za-z0-9\-]{3,50}$", enrollee_id.strip()))


def validate_phone_format(phone: str) -> bool:
    """Validate Nigerian phone format (basic check)."""
    cleaned = re.sub(r"[\s\-\(\)]", "", phone.strip())
    return bool(re.match(r"^(\+234|0)[0-9]{10}$", cleaned))


def validate_account_number_format(account_number: str) -> bool:
    """Validate bank account number (10 digits for Nigerian banks)."""
    return bool(re.match(r"^[0-9]{10}$", account_number.strip()))
