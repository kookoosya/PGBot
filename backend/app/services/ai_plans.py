"""Public AI tariff menu and feature flags."""

from __future__ import annotations

from dataclasses import dataclass

from app.config import get_settings

settings = get_settings()


@dataclass(frozen=True, slots=True)
class AIPlan:
    id: str
    name: str
    daily_limit: int
    price_rub: int
    period_days: int
    tagline: str
    features: tuple[str, ...]
    chat_modes: tuple[str, ...]
    model_id: str
    requires_login: bool
    requires_payment: bool


def build_ai_plans() -> list[AIPlan]:
    return [
        AIPlan(
            id="free",
            name="Бесплатно",
            daily_limit=settings.AI_FREE_DAILY_LIMIT,
            price_rub=0,
            period_days=1,
            tagline="Попробовать ИИ на сайте",
            features=(
                f"{settings.AI_FREE_DAILY_LIMIT} сообщений или картинок в день",
                "Базовый режим через наш сервер",
                "Без сохранения истории между днями",
            ),
            chat_modes=("chat",),
            model_id="gemini-flash",
            requires_login=False,
            requires_payment=False,
        ),
        AIPlan(
            id="trial",
            name="Пробный период",
            daily_limit=settings.AI_TRIAL_DAILY_LIMIT,
            price_rub=0,
            period_days=settings.AI_TRIAL_PERIOD_DAYS,
            tagline="7 дней после входа в аккаунт",
            features=(
                f"{settings.AI_TRIAL_DAILY_LIMIT} сообщений в день",
                "Умные модели Gemini через наш прокси — работает из России",
                "Режимы: чат, учёба, код",
                "Без оплаты зарубежных API с вашей карты",
            ),
            chat_modes=("chat", "study", "code"),
            model_id="gemini",
            requires_login=True,
            requires_payment=False,
        ),
        AIPlan(
            id="pro",
            name="ИИ Pro",
            daily_limit=settings.AI_PRO_DAILY_LIMIT,
            price_rub=settings.AI_PRO_PRICE,
            period_days=settings.AI_PRO_PERIOD_DAYS,
            tagline="Постоянный доступ через наш сервер",
            features=(
                f"До {settings.AI_PRO_DAILY_LIMIT} сообщений в день на аккаунт",
                "Gemini / Pollinations через встроенный прокси — без блокировок из РФ",
                "Режимы «Учёба» и «Код»",
                "Картинки в общем лимите",
                "Оплата переводом в рублях — без зарубежных подписок",
            ),
            chat_modes=("chat", "study", "code"),
            model_id="gemini",
            requires_login=True,
            requires_payment=True,
        ),
        AIPlan(
            id="pro_plus",
            name="ИИ Pro+",
            daily_limit=settings.AI_PRO_PLUS_DAILY_LIMIT,
            price_rub=settings.AI_PRO_PLUS_PRICE,
            period_days=settings.AI_PRO_PERIOD_DAYS,
            tagline="Для активных пользователей",
            features=(
                f"До {settings.AI_PRO_PLUS_DAILY_LIMIT} сообщений в день",
                "Приоритет на нашем AI-шлюзе",
                "Все режимы и картинки",
                "Подходит для ежедневной работы с текстами и кодом",
            ),
            chat_modes=("chat", "study", "code"),
            model_id="openai",
            requires_login=True,
            requires_payment=True,
        ),
    ]


def plan_by_id(plan_id: str) -> AIPlan | None:
    return next((plan for plan in build_ai_plans() if plan.id == plan_id), None)


def plan_to_dict(plan: AIPlan) -> dict:
    return {
        "id": plan.id,
        "name": plan.name,
        "daily_limit": plan.daily_limit,
        "price_rub": plan.price_rub,
        "period_days": plan.period_days,
        "tagline": plan.tagline,
        "features": list(plan.features),
        "chat_modes": list(plan.chat_modes),
        "model_id": plan.model_id,
        "requires_login": plan.requires_login,
        "requires_payment": plan.requires_payment,
    }


CHAT_MODE_LABELS = {
    "chat": "💬 Обычный чат",
    "study": "📚 Учёба и тексты",
    "code": "💻 Код",
}

CHAT_MODE_PROMPTS = {
    "study": (
        "\n\nРежим «Учёба»: помогай с учебными работами структурированно — план, тезисы, "
        "проверка логики и оформления. Не выдавай готовую работу целиком для сдачи без "
        "участия студента; объясняй и улучшай черновик."
    ),
    "code": (
        "\n\nРежим «Код»: пиши рабочий код с комментариями, объясняй ошибки, предлагай "
        "тесты и рефакторинг. Форматируй блоки кода с указанием языка."
    ),
}
