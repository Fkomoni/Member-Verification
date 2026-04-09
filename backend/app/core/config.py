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

    # WellaHealth API (acute medication fulfilment)
    WELLAHEALTH_BASE_URL: str = "https://staging.wellahealth.com/v1"
    WELLAHEALTH_PARTNER_CODE: str = ""
    WELLAHEALTH_CLIENT_ID: str = ""
    WELLAHEALTH_CLIENT_SECRET: str = ""

    # Google Maps / Geolocation API
    GOOGLE_MAPS_API_KEY: str = ""

    # Leadway WhatsApp routing numbers
    WHATSAPP_LAGOS_NUMBER: str = ""
    WHATSAPP_OUTSIDE_LAGOS_NUMBER: str = ""

    # WhatsApp Bot Webhook (existing Leadway bot)
    WHATSAPP_WEBHOOK_URL: str = ""
    WHATSAPP_VERIFY_TOKEN: str = ""
    WHATSAPP_APP_SECRET: str = ""

    # Anthropic API (LangChain AI drug classification)
    ANTHROPIC_API_KEY: str = ""

    model_config = {"env_file": ".env"}


settings = Settings()
