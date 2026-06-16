import enum


class EventCategory(str, enum.Enum):
    CULTURE = "culture"
    HOLIDAY = "holiday"
    SPORT = "sport"
    EDUCATION = "education"
    COMMUNITY = "community"
    TOURISM = "tourism"
    CINEMA = "cinema"
    OTHER = "other"


class EventRegion(str, enum.Enum):
    PUSHKIN_GORY = "pushkin_gory"
    PSKOV = "pskov"


EVENT_CATEGORY_LABELS = {
    EventCategory.CULTURE: "Культура",
    EventCategory.HOLIDAY: "Праздник",
    EventCategory.SPORT: "Спорт",
    EventCategory.EDUCATION: "Образование",
    EventCategory.COMMUNITY: "Общее",
    EventCategory.TOURISM: "Туризм",
    EventCategory.CINEMA: "Кино",
    EventCategory.OTHER: "Событие",
}

EVENT_REGION_LABELS = {
    EventRegion.PUSHKIN_GORY: "Пушкинские Горы",
    EventRegion.PSKOV: "Псков",
}
