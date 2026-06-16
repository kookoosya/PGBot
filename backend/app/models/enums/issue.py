import enum


class IssueStatus(str, enum.Enum):
    NEW = "NEW"
    UNDER_REVIEW = "UNDER_REVIEW"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    REJECTED = "REJECTED"
    ARCHIVED = "ARCHIVED"


class IssueCategory(str, enum.Enum):
    ROADS = "Дороги"
    LIGHTING = "Освещение"
    GARBAGE = "Мусор"
    WATER = "Вода"
    SEWERAGE = "Канализация"
    UTILITIES = "ЖКХ"
    LANDSCAPING = "Благоустройство"
    PUBLIC_TRANSPORT = "Общественный транспорт"
    SAFETY = "Безопасность"
    STRAY_ANIMALS = "Бездомные животные"
    SOCIAL_HELP = "Социальная помощь"
    ECOLOGY = "Экология"
    OTHER = "Другое"


class Priority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
