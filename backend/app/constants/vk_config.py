"""VK bot subscription presets and aliases."""

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
