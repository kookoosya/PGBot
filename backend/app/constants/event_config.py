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
    require_region_keywords: tuple[str, ...] = ()
    group_id: int = 0


# Multiple VK communities per region (resolved via groups.getById).
VK_EVENT_GROUPS: tuple[VkGroupPreset, ...] = (
    VkGroupPreset(
        screen_name="pushkinogorie",
        label="Музей-заповедник «Михайловское»",
        region=EventRegion.PUSHKIN_GORY,
        default_location="Пушкинские Горы, Михайловское",
        group_id=958262,
    ),
    VkGroupPreset(
        screen_name="pushkinskie_gory",
        label="Пушкинские Горы — туризм",
        region=EventRegion.PUSHKIN_GORY,
        default_location="Пушкинские Горы",
        group_id=22384906,
    ),
    VkGroupPreset(
        screen_name="club119250676",
        label="Вестник Пушкиногорья",
        region=EventRegion.PUSHKIN_GORY,
        default_location="Пушкинские Горы",
        group_id=119250676,
    ),
    VkGroupPreset(
        screen_name="gorodpskov",
        label="Администрация Пскова",
        region=EventRegion.PSKOV,
        default_location="Псков",
        group_id=29874422,
    ),
    VkGroupPreset(
        screen_name="kultyrnipskov",
        label="Управление культуры Пскова",
        region=EventRegion.PSKOV,
        default_location="Псков",
        group_id=216838258,
    ),
    VkGroupPreset(
        screen_name="pskovmuseum",
        label="Псковский музей-заповедник",
        region=EventRegion.PSKOV,
        default_location="Псков, Кремль",
        group_id=132819181,
    ),
    VkGroupPreset(
        screen_name="afipskov",
        label="Афиша Псков (кино, концерты)",
        region=EventRegion.PSKOV,
        default_location="Псков",
        group_id=39969164,
    ),
    VkGroupPreset(
        screen_name="club39969164",
        label="Афиша Псков (резерв)",
        region=EventRegion.PSKOV,
        default_location="Псков",
        group_id=39969164,
    ),
    VkGroupPreset(
        screen_name="220203925",
        label="Пушкиногорский журнал",
        region=EventRegion.PUSHKIN_GORY,
        default_location="Пушкинские Горы",
        group_id=220203925,
    ),
    VkGroupPreset(
        screen_name="club220027661",
        label="Туристско-информационный центр | Пушкинские Горы",
        region=EventRegion.PUSHKIN_GORY,
        default_location="Пушкинские Горы",
        group_id=220027661,
    ),
    VkGroupPreset(
        screen_name="club50667602",
        label="Пушкинский Заповедник",
        region=EventRegion.PUSHKIN_GORY,
        default_location="Пушкинские Горы",
        group_id=50667602,
    ),
    VkGroupPreset(
        screen_name="informpskov",
        label="ИнформПсков",
        region=EventRegion.PSKOV,
        default_location="Псков",
        group_id=39325015,
    ),
    VkGroupPreset(
        screen_name="drampush",
        label="Псковский театр драмы",
        region=EventRegion.PSKOV,
        default_location="Псков, театр",
        group_id=56134296,
    ),
    VkGroupPreset(
        screen_name="gkcpskov",
        label="Городской культурный центр Пскова",
        region=EventRegion.PSKOV,
        default_location="Псков, ГКЦ",
        group_id=20036616,
    ),
    VkGroupPreset(
        screen_name="club166260004",
        label="Администрация Пушкиногорского МО",
        region=EventRegion.PUSHKIN_GORY,
        default_location="Пушкинские Горы",
        group_id=166260004,
    ),
    VkGroupPreset(
        screen_name="club218787339",
        label="КДЦ Пушкиногорский",
        region=EventRegion.PUSHKIN_GORY,
        default_location="Пушкинские Горы, КДЦ",
        group_id=218787339,
    ),
    VkGroupPreset(
        screen_name="plnpsk",
        label="Псковская Лента Новостей",
        region=EventRegion.PSKOV,
        default_location="Псков",
        group_id=1205247,
        require_region_keywords=(
            "псков", "псковск", "пушкин", "пушкиногор", "михайловск",
            "бугров", "петергоф", "остров", "порхов", "печоры", "изборск",
        ),
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
    "cinema": ("кино", "фильм", "сеанс", "кинотеатр"),
    "holiday": ("праздник", "фестиваль", "ярмарка", "юбилей", "гарнец"),
    "culture": ("концерт", "выставк", "театр", "музей", "лекци", "спектакл", "фольклор", "театральн"),
    "sport": ("спорт", "турнир", "забег", "марафон"),
    "education": ("мастер-класс", "семинар", "обучен"),
    "tourism": ("экскурс", "маршрут", "турист"),
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
