from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    APP_NAME: str = "LeadwayHMO RxHub"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql://localhost/rxhub"

    # JWT
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_ADMIN_TOKEN_EXPIRE_MINUTES: int = 480

    # Prognosis API (PBM Backend)
    PROGNOSIS_API_BASE_URL: str = "https://prognosis-api.leadwayhealth.com/api"
    PROGNOSIS_USERNAME: str = ""
    PROGNOSIS_PASSWORD: str = ""
    PROGNOSIS_API_TIMEOUT: int = 30

    # OTP
    OTP_EXPIRE_MINUTES: int = 5
    OTP_MAX_ATTEMPTS: int = 3
    OTP_LENGTH: int = 6

    # SMS Gateway
    SMS_PROVIDER: str = "TERMII"
    SMS_API_KEY: str = ""
    SMS_SENDER_ID: str = "LeadwayHMO"

    # AWS S3
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_S3_BUCKET: str = "rxhub-uploads"
    AWS_S3_REGION: str = "eu-west-1"

    # Paystack
    PAYSTACK_SECRET_KEY: str = ""
    PAYSTACK_PUBLIC_KEY: str = ""

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3001,https://rxhub-member.onrender.com,https://rxhub-admin.onrender.com"

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
