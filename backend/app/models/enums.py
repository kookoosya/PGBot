import enum


class UserRole(str, enum.Enum):
    RESIDENT = "resident"
    MODERATOR = "moderator"
    ADMINISTRATION = "administration"
    SOCIAL_SERVICE = "social_service"
    SUPER_ADMIN = "super_admin"


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


class NotificationStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class NotificationPriority(str, enum.Enum):
    NORMAL = "normal"
    HIGH = "high"


class VerificationStatus(str, enum.Enum):
    NOT_REQUIRED = "not_required"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


OFFICIAL_ROLES = {
    UserRole.MODERATOR,
    UserRole.ADMINISTRATION,
    UserRole.SOCIAL_SERVICE,
}
