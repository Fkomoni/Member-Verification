from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Biometric Member Verification Portal"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/member_verification"

    # JWT
    SECRET_KEY: str = "CHANGE-THIS-TO-A-SECURE-RANDOM-KEY"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Encryption key for biometric templates (Fernet, 32-byte base64)
    BIOMETRIC_ENCRYPTION_KEY: str = "CHANGE-THIS-GENERATE-WITH-Fernet.generate_key()"

    # Futronic FS80H configuration
    FUTRONIC_SDK_AVAILABLE: str = "true"  # set "false" for dev/CI without scanner
    FUTRONIC_MATCH_THRESHOLD: int = 800   # 0-10000, higher = stricter
    REQUIRE_LFD: bool = True              # enforce Live Finger Detection

    # Prognosis core system integration (Leadway Health)
    PROGNOSIS_BASE_URL: str = "https://prognosis-api.leadwayhealth.com"
    PROGNOSIS_USERNAME: str = ""
    PROGNOSIS_PASSWORD: str = ""

    # Authorization code settings
    AUTH_CODE_EXPIRY_HOURS: int = 72
    AUTH_CODE_LENGTH: int = 8  # chars per segment (format: LH-XXXX-XXXX)
    AUTH_CODE_MAX_VALIDATION_ATTEMPTS: int = 5  # per IP per 15 min

    # Claims email — sent via Prognosis SendEmailAlert API (no SMTP needed)
    CLAIMS_EMAIL: str = ""

    model_config = {"env_file": ".env"}


settings = Settings()
