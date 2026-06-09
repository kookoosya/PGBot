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

    # Redis (rate limiting, shared counters across workers)
    REDIS_URL: str = "redis://redis:6379/0"
    REDIS_SOCKET_TIMEOUT: float = 2.0

    # JWT
    SECRET_KEY: str = "change-me-in-production-use-long-random-string"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 14
    LOGIN_MAX_ATTEMPTS: int = 5
    LOGIN_LOCKOUT_MINUTES: int = 30

    # Owner-only admin panel (comma-separated logins; empty = SUPER_ADMIN_USERNAME)
    OWNER_USERNAME: str = ""
    SUPER_ADMIN_USERNAME: str = "admin"

    # Gemini
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"
    POLLINATIONS_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""
    AI_IMAGE_DIR: str = "/tmp/pgbot-ai-images"

    # VK
    VK_GROUP_TOKEN: str = ""
    VK_CONFIRMATION_CODE: str = ""
    VK_SECRET_KEY: str = ""
    VK_API_VERSION: str = "5.199"
    VK_GROUP_URL: str = "https://vk.com"
    VK_ADMIN_PEER_ID: str = ""
    PUBLIC_SITE_URL: str = "https://pushkinskie-gory.ru"

    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_ADMIN_CHAT_ID: str = ""

    # CORS
    CORS_ORIGINS: str = (
        "http://localhost:5173,http://localhost:3000,http://localhost,"
        "https://pushkinskie-gory.ru,https://www.pushkinskie-gory.ru,"
        "https://192-210-213-135.sslip.io"
    )

    # Rate limiting (SlowAPI + Redis storage when REDIS_URL is set)
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_STORAGE: str = "auto"  # auto | redis | memory
    RATE_LIMIT_KEY_PREFIX: str = "pgbot:rl:"
    RATE_LIMIT: str = "120/minute"
    LOGIN_RATE_LIMIT: str = "10/minute"
    REFRESH_RATE_LIMIT: str = "30/minute"
    ISSUE_RATE_LIMIT: str = "6/hour"
    CLASSIFIED_RATE_LIMIT: str = "12/hour"
    AI_CHAT_RATE_LIMIT: str = "40/hour"
    AI_IMAGE_RATE_LIMIT: str = "15/hour"
    BOOKING_RATE_LIMIT: str = "8/hour"
    FEEDBACK_RATE_LIMIT: str = "8/hour"
    VK_CALLBACK_RATE_LIMIT: str = "120/minute"
    REGISTER_RATE_LIMIT: str = "5/hour"
    VERIFICATION_RATE_LIMIT: str = "5/hour"
    PLACE_REPORT_RATE_LIMIT: str = "20/hour"
    PLACE_COMPLAINT_RATE_LIMIT: str = "10/hour"
    CLASSIFIED_VIEW_RATE_LIMIT: str = "60/minute"
    HEALTH_RATE_LIMIT: str = "30/minute"

    # Duplicate threshold
    DUPLICATE_THRESHOLD: float = 0.80

    # Public AI chat limits
    AI_FREE_DAILY_LIMIT: int = 30
    AI_VK_DAILY_LIMIT: int = 20
    AI_MAX_MESSAGE_LENGTH: int = 1000

    # Payment / support (card transfer)
    PAYMENT_CARD_NUMBER: str = ""
    PAYMENT_CARD_HOLDER: str = "Портал ПГ"
    PAYMENT_BANK_NAME: str = "Сбербанк"
    PAYMENT_DESCRIPTION: str = "Портал посёлка ПГ"
    PAYMENT_AMOUNT_SUGGESTED: int = 150
    PAYMENT_CONTACT_EMAIL: str = "support@pushkinskie-gory.local"

    # Classified ads: 3 free, then 150 ₽ per ad per 30 days
    CLASSIFIED_FREE_LIMIT: int = 3
    CLASSIFIED_PLACEMENT_FEE: int = 150
    CLASSIFIED_PERIOD_DAYS: int = 30
    CLASSIFIED_PAYMENT_DESCRIPTION: str = "Объявление Пушкинские Горы"

    # Map / OSM sync (Pushkinogorsky district center)
    MAP_CENTER_LAT: float = 57.0267
    MAP_CENTER_LNG: float = 28.9100
    MAP_SYNC_RADIUS_KM: float = 15.0
    MAP_AUTO_SYNC_HOURS: int = 6

    # Yandex Maps Organization Search API (optional — enriches ratings)
    YANDEX_MAPS_API_KEY: str = ""

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def owner_usernames(self) -> set[str]:
        raw = self.OWNER_USERNAME.strip() or self.SUPER_ADMIN_USERNAME
        return {u.strip() for u in raw.split(",") if u.strip()}

    @property
    def rate_limit_storage_uri(self) -> str | None:
        """Resolve SlowAPI storage URI from settings."""
        mode = self.RATE_LIMIT_STORAGE.strip().lower()
        if mode == "memory":
            return None
        if mode == "redis":
            if not self.REDIS_URL:
                raise RuntimeError("RATE_LIMIT_STORAGE=redis requires REDIS_URL")
            return self.REDIS_URL
        if self.REDIS_URL:
            return self.REDIS_URL
        return None


@lru_cache
def get_settings() -> Settings:
    return Settings()
