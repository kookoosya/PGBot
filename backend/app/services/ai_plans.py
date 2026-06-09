"""Public AI tariff menu and feature flags."""

from __future__ import annotations

from dataclasses import dataclass

from app.config import get_settings

settings = get_settings()

PUBLIC_PLAN_IDS = ("trial", "pro")


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
            name="Гость",
            daily_limit=settings.AI_FREE_DAILY_LIMIT,
            price_rub=0,
            period_days=1,
            tagline="Без регистрации",
            features=(
                f"{settings.AI_FREE_DAILY_LIMIT} сообщений или картинок в день",
                "Только обычный чат",
            ),
            chat_modes=("chat",),
            model_id="gemini-flash",
            requires_login=False,
            requires_payment=False,
        ),
        AIPlan(
            id="trial",
            name="Пробный",
            daily_limit=settings.AI_TRIAL_DAILY_LIMIT,
            price_rub=0,
            period_days=settings.AI_TRIAL_PERIOD_DAYS,
            tagline=f"{settings.AI_TRIAL_PERIOD_DAYS} дней после входа",
            features=(
                f"{settings.AI_TRIAL_DAILY_LIMIT} сообщений в день",
                "Режимы: чат, учёба, код",
                "Без оплаты — включается автоматически",
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
            tagline="Платный доступ",
            features=(
                f"До {settings.AI_PRO_DAILY_LIMIT} сообщений в день",
                "Режимы «Учёба» и «Код»",
                "Картинки в общем лимите",
                "Оплата переводом — доступ автоматически после перевода с кодом",
            ),
            chat_modes=("chat", "study", "code"),
            model_id="gemini",
            requires_login=True,
            requires_payment=True,
        ),
    ]


def plan_by_id(plan_id: str) -> AIPlan | None:
    return next((plan for plan in build_ai_plans() if plan.id == plan_id), None)


def effective_daily_limit(plan: AIPlan) -> int:
    return min(plan.daily_limit, settings.AI_MAX_DAILY_LIMIT)


def plan_to_dict(plan: AIPlan) -> dict:
    return {
        "id": plan.id,
        "name": plan.name,
        "daily_limit": effective_daily_limit(plan),
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
