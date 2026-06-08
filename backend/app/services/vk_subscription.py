"""VK classified subscription presets and category matching."""

from __future__ import annotations

from app.models.enums import (
    CLASSIFIED_LABELS,
    ClassifiedCategory,
    JOB_CLASSIFIED_CATEGORIES,
    SERVICE_CLASSIFIED_CATEGORIES,
)
from app.models.vk_subscriber import VkSubscriber

SUBSCRIPTION_PRESETS: dict[str, str] = {
    "all": "все объявления",
    "jobs": "работа и вакансии",
    "services": "услуги и мастера",
    "firewood": "дрова и колка",
    "garden": "огород / перепашка",
    "neighbor": "сосед помогает",
}

SUBSCRIPTION_ALIASES: dict[str, str] = {
    "все": "all",
    "работа": "jobs",
    "вакансии": "jobs",
    "услуги": "services",
    "мастера": "services",
    "дрова": "firewood",
    "огород": "garden",
    "сосед": "neighbor",
    "помощь": "neighbor",
    "neighbor_help": "neighbor",
}

VALID_CATEGORY_VALUES = {category.value for category in ClassifiedCategory}


def normalize_subscription_categories(raw: str) -> tuple[str, str]:
    """Return stored categories key and human label."""
    value = (raw or "all").lower().strip() or "all"
    if value in SUBSCRIPTION_ALIASES:
        value = SUBSCRIPTION_ALIASES[value]

    if value in SUBSCRIPTION_PRESETS:
        return value, SUBSCRIPTION_PRESETS[value]

    parts = [part.strip() for part in value.split(",") if part.strip()]
    resolved: list[str] = []
    for part in parts:
        part = SUBSCRIPTION_ALIASES.get(part, part)
        if part in SUBSCRIPTION_PRESETS:
            return part, SUBSCRIPTION_PRESETS[part]
        if part in VALID_CATEGORY_VALUES:
            resolved.append(part)

    if not resolved:
        return "all", SUBSCRIPTION_PRESETS["all"]

    key = ",".join(dict.fromkeys(resolved))
    if len(resolved) == 1:
        category = ClassifiedCategory(resolved[0])
        label = CLASSIFIED_LABELS.get(category, resolved[0])
        return key, label
    labels = [CLASSIFIED_LABELS.get(ClassifiedCategory(v), v) for v in resolved[:3]]
    suffix = "…" if len(resolved) > 3 else ""
    return key, ", ".join(labels) + suffix


def subscriber_wants_category(sub: VkSubscriber, category: ClassifiedCategory | str) -> bool:
    """Return whether subscriber wants notifications for the given classified category."""
    cats = (sub.categories or "all").lower()
    cat_val = category.value if hasattr(category, "value") else str(category)

    if cats == "all":
        return True
    if cats == "jobs":
        return category in JOB_CLASSIFIED_CATEGORIES if isinstance(category, ClassifiedCategory) else cat_val.startswith("job")
    if cats == "services":
        return category in SERVICE_CLASSIFIED_CATEGORIES if isinstance(category, ClassifiedCategory) else cat_val in {c.value for c in SERVICE_CLASSIFIED_CATEGORIES}
    if cats == "firewood":
        return cat_val == ClassifiedCategory.FIREWOOD.value
    if cats == "garden":
        return cat_val == ClassifiedCategory.GARDEN.value
    if cats == "neighbor":
        return cat_val == ClassifiedCategory.NEIGHBOR_HELP.value

    allowed = {part.strip() for part in cats.split(",") if part.strip()}
    return cat_val in allowed


def subscription_options_text() -> str:
    lines = ["Доступные подписки:"]
    for key, label in SUBSCRIPTION_PRESETS.items():
        lines.append(f"• «подписка {key}» — {label}")
    lines.append("• «подписка firewood,garden» — несколько категорий")
    return "\n".join(lines)
