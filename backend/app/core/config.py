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

    # Paystack (bank account validation)
    PAYSTACK_SECRET_KEY: str = ""

    # Email — sent via Prognosis SendEmailAlert API (no SMTP needed)
    CLAIMS_TEAM_EMAIL: str = ""  # claims team receives CC of every claim submission

    model_config = {"env_file": ".env"}


settings = Settings()
