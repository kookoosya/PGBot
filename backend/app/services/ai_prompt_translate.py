"""Перевод русских промптов в английские для image API."""

import re

# Частые слова в запросах жителей → англ. теги для Flux
RU_IMAGE_TAGS: dict[str, str] = {
    "изба": "cozy wooden russian izba hut",
    "усадьба": "russian manor estate",
    "снег": "snow winter",
    "зим": "winter snowy",
    "закат": "sunset golden hour",
    "рассвет": "sunrise morning light",
    "пушкин": "pushkin literary memorial",
    "памятник": "monument statue park",
    "парк": "green park alleys",
    "деревн": "russian village countryside",
    "посёлок": "small russian town",
    "русск": "traditional russian style",
    "лет": "summer meadow",
    "озер": "lake reflection",
    "река": "river landscape",
    "лес": "pine forest",
    "церков": "orthodox church dome",
    "лавр": "monastery lavra",
    "михайловск": "mikhailovskoye estate museum",
    "колокол": "church bells",
    "поле": "wheat field",
    "дорог": "country road",
    "кот": "cat",
    "собак": "dog",
    "цвет": "flowers blooming",
    "ноч": "night stars",
    "туман": "morning fog",
    "уют": "cozy warm atmosphere",
}


def image_prompt_english(prompt: str) -> str:
    """Собрать английский промпт из русского описания."""
    low = prompt.lower()
    tags: list[str] = []
    for ru, en in RU_IMAGE_TAGS.items():
        if ru in low:
            tags.append(en)

    # Уже есть латиница — оставляем как есть, но добавляем стиль
    has_latin = bool(re.search(r"[a-zA-Z]{3}", prompt))
    if has_latin and not tags:
        return f"{prompt.strip()}, detailed scenic illustration, high quality"

    if tags:
        unique = list(dict.fromkeys(tags))
        scene = ", ".join(unique)
        return f"{scene}, russian countryside pushkin hills, cinematic illustration, detailed"

    return (
        "scenic russian village landscape pushkin hills, "
        "traditional wooden architecture, artistic detailed illustration"
    )
