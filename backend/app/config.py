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
    # User token with groups scope — required to read afipskov/other walls for posters
    VK_USER_TOKEN: str = ""
    VK_CONFIRMATION_CODE: str = ""
    VK_SECRET_KEY: str = ""
    VK_API_VERSION: str = "5.199"
    VK_GROUP_URL: str = "https://vk.com"
    VK_GROUP_ID: str = ""
    VK_ADMIN_PEER_ID: str = ""
    # Auto-post relevant events to community wall after sync
    VK_WALL_POST_ENABLED: bool = False
    VK_WALL_POST_MAX_PER_RUN: int = 1
    VK_WALL_POST_MIN_SCORE: int = 65
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

    # Rate limiting
    RATE_LIMIT: str = "120/minute"
    ISSUE_RATE_LIMIT: str = "6/hour"
    CLASSIFIED_RATE_LIMIT: str = "12/hour"
    AI_CHAT_RATE_LIMIT: str = "40/hour"
    AI_IMAGE_RATE_LIMIT: str = "15/hour"
    BOOKING_RATE_LIMIT: str = "8/hour"
    FEEDBACK_RATE_LIMIT: str = "8/hour"
    VK_CALLBACK_RATE_LIMIT: str = "120/minute"

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

    # Weather (Open-Meteo — free, no API key)
    WEATHER_TIMEZONE: str = "Europe/Moscow"
    WEATHER_CACHE_TTL_SECONDS: int = 1800
    WEATHER_HOURLY_HOURS: int = 24
    WEATHER_FORECAST_DAYS: int = 2

    # Yandex Maps Organization Search API (optional — enriches ratings)
    YANDEX_MAPS_API_KEY: str = ""

    # TimePad events (https://dev.timepad.ru/)
    TIMEPAD_API_TOKEN: str = ""

    # PRO.Культура.РФ (https://pro.culture.ru/documentation/export_API_PRO.pdf)
    PROCULTURE_API_KEY: str = ""
    PROCULTURE_PSKOV_LOCALE_ID: int = 0

    # Kinopoisk Unofficial API — posters for cinema (https://kinopoiskapiunofficial.tech/signup)
    KINOPOISK_API_TOKEN: str = ""

    # Auto-sync village events from external sources (hours; 0 = disabled)
    EVENT_SYNC_INTERVAL_HOURS: int = 12

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def owner_usernames(self) -> set[str]:
        raw = self.OWNER_USERNAME.strip() or self.SUPER_ADMIN_USERNAME
        return {u.strip() for u in raw.split(",") if u.strip()}


@lru_cache
def get_settings() -> Settings:
    return Settings()
