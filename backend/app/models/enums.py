import enum


class UserRole(str, enum.Enum):
    RESIDENT = "resident"
    MODERATOR = "moderator"
    ADMINISTRATION = "administration"
    SOCIAL_SERVICE = "social_service"
    SERVICE_PROVIDER = "service_provider"
    SUPER_ADMIN = "super_admin"


class ServiceType(str, enum.Enum):
    MANICURE = "manicure"
    PEDICURE = "pedicure"
    HAIRCUT = "haircut"
    HAIR_COLOR = "hair_color"
    MASSAGE = "massage"
    COSMETOLOGY = "cosmetology"
    BROWS = "brows"
    OTHER = "other"


SERVICE_TYPE_LABELS = {
    ServiceType.MANICURE: "Маникюр",
    ServiceType.PEDICURE: "Педикюр",
    ServiceType.HAIRCUT: "Стрижка",
    ServiceType.HAIR_COLOR: "Окрашивание",
    ServiceType.MASSAGE: "Массаж",
    ServiceType.COSMETOLOGY: "Косметология",
    ServiceType.BROWS: "Брови/ресницы",
    ServiceType.OTHER: "Другое",
}


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


class PlaceCategory(str, enum.Enum):
    SHOP = "shop"
    SUPERMARKET = "supermarket"
    PHARMACY = "pharmacy"
    CAFE = "cafe"
    RESTAURANT = "restaurant"
    BANK = "bank"
    POST = "post"
    SCHOOL = "school"
    HOSPITAL = "hospital"
    GOVERNMENT = "government"
    TRANSPORT = "transport"
    CULTURE = "culture"
    HOTEL = "hotel"
    GAS = "gas"
    BEAUTY = "beauty"
    OTHER = "other"


class ShopComplaintType(str, enum.Enum):
    PRICE_TAG_FRAUD = "price_tag_fraud"
    RECEIPT_FRAUD = "receipt_fraud"
    OVERCHARGE = "overcharge"
    NO_RECEIPT = "no_receipt"
    EXPIRED_PRODUCT = "expired_product"
    SHORT_WEIGHT = "short_weight"
    OTHER = "other"


PLACE_CATEGORY_LABELS = {
    PlaceCategory.SHOP: "Магазин",
    PlaceCategory.SUPERMARKET: "Супермаркет",
    PlaceCategory.PHARMACY: "Аптека",
    PlaceCategory.CAFE: "Кафе",
    PlaceCategory.RESTAURANT: "Ресторан",
    PlaceCategory.BANK: "Банк",
    PlaceCategory.POST: "Почта",
    PlaceCategory.SCHOOL: "Школа",
    PlaceCategory.HOSPITAL: "Медицина",
    PlaceCategory.GOVERNMENT: "Госучреждение",
    PlaceCategory.TRANSPORT: "Транспорт",
    PlaceCategory.CULTURE: "Культура",
    PlaceCategory.HOTEL: "Гостиница",
    PlaceCategory.GAS: "АЗС",
    PlaceCategory.BEAUTY: "Красота/услуги",
    PlaceCategory.OTHER: "Другое",
}

SHOP_COMPLAINT_LABELS = {
    ShopComplaintType.PRICE_TAG_FRAUD: "Цена на полке ≠ на кассе",
    ShopComplaintType.RECEIPT_FRAUD: "Обман в чеке",
    ShopComplaintType.OVERCHARGE: "Завышение цены",
    ShopComplaintType.NO_RECEIPT: "Не выдали чек",
    ShopComplaintType.EXPIRED_PRODUCT: "Просроченный товар",
    ShopComplaintType.SHORT_WEIGHT: "Недовес",
    ShopComplaintType.OTHER: "Другое",
}


OFFICIAL_ROLES = {
    UserRole.MODERATOR,
    UserRole.ADMINISTRATION,
    UserRole.SOCIAL_SERVICE,
}
