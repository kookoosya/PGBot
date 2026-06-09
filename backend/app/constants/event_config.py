"""Event feed configuration — regions, VK groups, TimePad, KudaGo."""

from dataclasses import dataclass

from app.models.enums import EventRegion

EVENT_REGION_LABELS: dict[EventRegion, str] = {
    EventRegion.PUSHKIN_GORY: "Пушкинские Горы",
    EventRegion.PSKOV: "Псков",
}


@dataclass(frozen=True, slots=True)
class VkGroupPreset:
    """VK community to scan for regional events."""

    screen_name: str
    label: str
    region: EventRegion
    default_location: str


# Multiple VK communities per region (resolved via groups.getById).
VK_EVENT_GROUPS: tuple[VkGroupPreset, ...] = (
    VkGroupPreset(
        screen_name="pushkinogorie",
        label="Музей-заповедник «Михайловское»",
        region=EventRegion.PUSHKIN_GORY,
        default_location="Пушкинские Горы, Михайловское",
    ),
    VkGroupPreset(
        screen_name="pushkinskie_gory",
        label="Пушкинские Горы — туризм",
        region=EventRegion.PUSHKIN_GORY,
        default_location="Пушкинские Горы",
    ),
    VkGroupPreset(
        screen_name="pushkiny",
        label="Посёлок Пушкинские Горы",
        region=EventRegion.PUSHKIN_GORY,
        default_location="Пушкинские Горы",
    ),
    VkGroupPreset(
        screen_name="gorodpskov",
        label="Администрация Пскова",
        region=EventRegion.PSKOV,
        default_location="Псков",
    ),
    VkGroupPreset(
        screen_name="kulturapscov",
        label="Управление культуры Пскова",
        region=EventRegion.PSKOV,
        default_location="Псков",
    ),
    VkGroupPreset(
        screen_name="pskovmuseum",
        label="Псковский музей-заповедник",
        region=EventRegion.PSKOV,
        default_location="Псков, Кремль",
    ),
    VkGroupPreset(
        screen_name="afipskov",
        label="Афиша Псков (кино, концерты)",
        region=EventRegion.PSKOV,
        default_location="Псков",
    ),
    VkGroupPreset(
        screen_name="club39969164",
        label="Афиша Псков (резерв)",
        region=EventRegion.PSKOV,
        default_location="Псков",
    ),
    VkGroupPreset(
        screen_name="220203925",
        label="Пушкиногорский журнал",
        region=EventRegion.PUSHKIN_GORY,
        default_location="Пушкинские Горы",
    ),
    VkGroupPreset(
        screen_name="informpskov",
        label="ИнформПсков",
        region=EventRegion.PSKOV,
        default_location="Псков",
    ),
    VkGroupPreset(
        screen_name="teatrpskov",
        label="Псковский академический театр",
        region=EventRegion.PSKOV,
        default_location="Псков, театр",
    ),
    VkGroupPreset(
        screen_name="dkpskov",
        label="Дворец культуры Пскова",
        region=EventRegion.PSKOV,
        default_location="Псков",
    ),
)

# Legacy single-group map (kept for backward-compatible imports).
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

# TimePad — cities and keywords for Pskov region (https://dev.timepad.ru/api/get-v1-events).
TIMEPAD_CITY_FILTERS: tuple[str, ...] = (
    "Псков",
    "Пушкинские Горы",
    "Пушкиногорье",
    "Псковская область",
)

TIMEPAD_KEYWORD_FILTERS: tuple[str, ...] = (
    "Псков",
    "Пушкинские",
    "Пушкиногор",
)

# KudaGo location slugs (https://kudago.com/public-api/v1.4/locations/).
# Note: as of 2026 KudaGo public API no longer lists Pskov — sync returns empty gracefully.
KUDAGO_LOCATION_PRESETS: dict[EventRegion, dict[str, str]] = {
    EventRegion.PSKOV: {
        "location_slug": "pskov",
        "label": "Псков",
        "default_location": "Псков",
    },
}

KUDAGO_CATEGORY_MAP: dict[str, str] = {
    "cinema": "cinema",
    "concert": "culture",
    "festival": "holiday",
    "exhibition": "culture",
    "theater": "culture",
    "education": "education",
    "sport": "sport",
    "tour": "tourism",
}

EVENT_CATEGORY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "cinema": ("кино", "фильм", "кинотеатр", "сеанс", "премьера фильма"),
    "holiday": ("праздник", "фестиваль", "ярмарка", "юбилей", "ёлка", "елка"),
    "culture": (
        "концерт", "выставк", "театр", "музей", "лекци", "спектакл",
        "салон", "программ", "литератур", "филармон", "балет", "опер",
        "хоров", "музык", "вечер", "премьер",
        "планетар", "полнокупольн",
    ),
    "sport": ("спорт", "турнир", "забег", "марафон"),
    "education": ("мастер-класс", "семинар", "обучен", "книжн", "мастерск"),
    "tourism": ("экскурс", "маршрут", "турист", "поход", "кремл"),
}

TIMEPAD_CATEGORY_MAP: dict[str, str] = {
    "концерт": "culture",
    "выставк": "culture",
    "театр": "culture",
    "лекци": "education",
    "мастер": "education",
    "фестиваль": "holiday",
    "ярмарк": "holiday",
    "спорт": "sport",
    "кино": "cinema",
    "экскурс": "tourism",
}
