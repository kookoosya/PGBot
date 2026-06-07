from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    APP_NAME: str = "Пушкинские Горы — портал посёлка"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@postgres:5432/narodny_kontrol"
    DATABASE_URL_SYNC: str = "postgresql://postgres:postgres@postgres:5432/narodny_kontrol"

    # JWT
    SECRET_KEY: str = "change-me-in-production-use-long-random-string"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 4
    LOGIN_MAX_ATTEMPTS: int = 5
    LOGIN_LOCKOUT_MINUTES: int = 30
    LOGIN_RATE_LIMIT: str = "10/minute"

    # Gemini
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"

    # VK
    VK_GROUP_TOKEN: str = ""
    VK_CONFIRMATION_CODE: str = ""
    VK_SECRET_KEY: str = ""
    VK_API_VERSION: str = "5.199"

    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_ADMIN_CHAT_ID: str = ""

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://localhost"

    # Rate limiting
    RATE_LIMIT: str = "100/minute"

    # Duplicate threshold
    DUPLICATE_THRESHOLD: float = 0.80

    # Public AI chat limits
    AI_FREE_DAILY_LIMIT: int = 30
    AI_VK_DAILY_LIMIT: int = 20
    AI_MAX_MESSAGE_LENGTH: int = 1000

    # Payment / support (card transfer)
    PAYMENT_CARD_NUMBER: str = "2204240170359972"
    PAYMENT_CARD_HOLDER: str = "Портал ПГ"
    PAYMENT_BANK_NAME: str = "Сбербанк"
    PAYMENT_DESCRIPTION: str = "Портал посёлка ПГ"
    PAYMENT_AMOUNT_SUGGESTED: int = 150
    PAYMENT_CONTACT_EMAIL: str = "support@pushkinskie-gory.local"

    # Classified ads placement fee
    CLASSIFIED_PLACEMENT_FEE: int = 150
    CLASSIFIED_PAYMENT_DESCRIPTION: str = "Объявление Пушкинские Горы"

    # Map / OSM sync (Pushkinogorsky district center)
    MAP_CENTER_LAT: float = 57.0267
    MAP_CENTER_LNG: float = 28.9100
    MAP_SYNC_RADIUS_KM: float = 15.0
    MAP_AUTO_SYNC_HOURS: int = 24

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
