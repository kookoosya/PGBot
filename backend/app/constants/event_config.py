"""Event feed configuration — regions and VK source presets."""

from app.models.enums import EventRegion

EVENT_REGION_LABELS: dict[EventRegion, str] = {
    EventRegion.PUSHKIN_GORY: "Пушкинские Горы",
    EventRegion.PSKOV: "Псков",
}

# Official VK communities to sync (screen names; resolved via groups.getById).
VK_EVENT_SOURCE_PRESETS: dict[EventRegion, dict[str, str]] = {
    EventRegion.PUSHKIN_GORY: {
        "screen_name": "pushkinogorie",
        "label": "Музей-заповедник Пушкина",
        "default_location": "Пушкинские Горы",
    },
    EventRegion.PSKOV: {
        "screen_name": "gorodpskov",
        "label": "Администрация Пскова",
        "default_location": "Псков",
    },
}

# Keywords for automatic category detection when syncing from VK.
EVENT_CATEGORY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "cinema": ("кино", "фильм", "сеанс", "кинотеатр"),
    "holiday": ("праздник", "фестиваль", "ярмарка", "юбилей"),
    "culture": ("концерт", "выставк", "театр", "музей", "лекци"),
    "sport": ("спорт", "турнир", "забег", "марафон"),
    "education": ("мастер-класс", "семинар", "обучен"),
    "tourism": ("экскурс", "маршрут", "турист"),
}
