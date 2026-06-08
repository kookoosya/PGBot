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


class CatalogCategory(str, enum.Enum):
    GARDEN = "garden"
    FIREWOOD = "firewood"
    GRASS_MOWING = "grass_mowing"
    DELIVERY = "delivery"
    HANDYMAN = "handyman"
    SNOW_REMOVAL = "snow_removal"
    CONSTRUCTION = "construction"
    BEAUTY = "beauty"
    TUTORING = "tutoring"
    TRANSPORT = "transport"
    AVITO = "avito"
    OTHER = "other"


class CatalogSource(str, enum.Enum):
    REFERENCE = "reference"
    AVITO = "avito"
    INTERNAL = "internal"


CATALOG_CATEGORY_LABELS = {
    CatalogCategory.GARDEN: "Огород / дача",
    CatalogCategory.FIREWOOD: "Дрова / колка",
    CatalogCategory.GRASS_MOWING: "Покос травы",
    CatalogCategory.DELIVERY: "Доставка / вывоз",
    CatalogCategory.HANDYMAN: "Разные работы",
    CatalogCategory.SNOW_REMOVAL: "Уборка снега",
    CatalogCategory.CONSTRUCTION: "Строительство / ремонт",
    CatalogCategory.BEAUTY: "Красота / уход",
    CatalogCategory.TUTORING: "Обучение / репетитор",
    CatalogCategory.TRANSPORT: "Перевозки / грузчики",
    CatalogCategory.AVITO: "На Авито",
    CatalogCategory.OTHER: "Другое",
}

class ClassifiedCategory(str, enum.Enum):
    GARDEN = "garden"
    FIREWOOD = "firewood"
    GRASS_MOWING = "grass_mowing"
    DELIVERY = "delivery"
    HANDYMAN = "handyman"
    SNOW_REMOVAL = "snow_removal"
    CONSTRUCTION = "construction"
    CONSTRUCTION_VACANCY = "construction_vacancy"
    CONSTRUCTION_OFFER = "construction_offer"
    TUTORING = "tutoring"
    RENT = "rent"
    SALE = "sale"
    JOB = "job"
    JOB_TOURISM = "job_tourism"
    JOB_TRADE = "job_trade"
    JOB_AGRICULTURE = "job_agriculture"
    JOB_SEASONAL = "job_seasonal"
    JOB_DRIVER = "job_driver"
    JOB_JKH = "job_jkh"
    JOB_CULTURE = "job_culture"
    JOB_SOCIAL = "job_social"
    JOB_EDUCATION = "job_education"
    OTHER = "other"


# Категории объявлений в едином каталоге услуг
SERVICE_CLASSIFIED_CATEGORIES = {
    ClassifiedCategory.GARDEN,
    ClassifiedCategory.FIREWOOD,
    ClassifiedCategory.GRASS_MOWING,
    ClassifiedCategory.DELIVERY,
    ClassifiedCategory.HANDYMAN,
    ClassifiedCategory.SNOW_REMOVAL,
    ClassifiedCategory.CONSTRUCTION,
    ClassifiedCategory.CONSTRUCTION_OFFER,
    ClassifiedCategory.TUTORING,
    ClassifiedCategory.OTHER,
}

JOB_CLASSIFIED_CATEGORIES = {
    ClassifiedCategory.JOB,
    ClassifiedCategory.CONSTRUCTION_VACANCY,
    ClassifiedCategory.JOB_TOURISM,
    ClassifiedCategory.JOB_TRADE,
    ClassifiedCategory.JOB_AGRICULTURE,
    ClassifiedCategory.JOB_SEASONAL,
    ClassifiedCategory.JOB_DRIVER,
    ClassifiedCategory.JOB_JKH,
    ClassifiedCategory.JOB_CULTURE,
    ClassifiedCategory.JOB_SOCIAL,
    ClassifiedCategory.JOB_EDUCATION,
}


class ClassifiedPaymentStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


CLASSIFIED_LABELS = {
    ClassifiedCategory.GARDEN: "Огород / перепашка",
    ClassifiedCategory.FIREWOOD: "Дрова / колка",
    ClassifiedCategory.GRASS_MOWING: "Покос травы",
    ClassifiedCategory.DELIVERY: "Доставка",
    ClassifiedCategory.HANDYMAN: "Разные работы",
    ClassifiedCategory.SNOW_REMOVAL: "Уборка снега",
    ClassifiedCategory.CONSTRUCTION: "Строительство / ремонт",
    ClassifiedCategory.CONSTRUCTION_VACANCY: "Строительство: вакансии",
    ClassifiedCategory.CONSTRUCTION_OFFER: "Строительство: предложения",
    ClassifiedCategory.TUTORING: "Услуги / обучение",
    ClassifiedCategory.RENT: "Аренда",
    ClassifiedCategory.SALE: "Продажа",
    ClassifiedCategory.JOB: "Работа (другое)",
    ClassifiedCategory.JOB_TOURISM: "Туризм / гостиницы",
    ClassifiedCategory.JOB_TRADE: "Магазины / торговля",
    ClassifiedCategory.JOB_AGRICULTURE: "Сельхоз / фермы",
    ClassifiedCategory.JOB_SEASONAL: "Сезонная подработка",
    ClassifiedCategory.JOB_DRIVER: "Водитель / перевозки",
    ClassifiedCategory.JOB_JKH: "ЖКХ / коммунальные",
    ClassifiedCategory.JOB_CULTURE: "Музей / культура",
    ClassifiedCategory.JOB_SOCIAL: "Медицина / соцсфера",
    ClassifiedCategory.JOB_EDUCATION: "Образование / дети",
    ClassifiedCategory.OTHER: "Другое",
}


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
    RENTAL = "rental"
    GAS = "gas"
    BEAUTY = "beauty"
    TYRE = "tyre"
    AUTO = "auto"
    TAXI = "taxi"
    PARKING = "parking"
    OTHER = "other"


class ShopComplaintType(str, enum.Enum):
    PRICE_TAG_FRAUD = "price_tag_fraud"
    RECEIPT_FRAUD = "receipt_fraud"
    OVERCHARGE = "overcharge"
    NO_RECEIPT = "no_receipt"
    EXPIRED_PRODUCT = "expired_product"
    SHORT_WEIGHT = "short_weight"
    OTHER = "other"
    MAP_WRONG_HOURS = "map_wrong_hours"
    MAP_WRONG_PHONE = "map_wrong_phone"
    MAP_CLOSED = "map_closed"
    MAP_WRONG_ADDRESS = "map_wrong_address"
    MAP_OTHER = "map_other"


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
    PlaceCategory.RENTAL: "Посуточно",
    PlaceCategory.GAS: "АЗС",
    PlaceCategory.BEAUTY: "Красота/услуги",
    PlaceCategory.TYRE: "Шиномонтаж",
    PlaceCategory.AUTO: "Автосервис",
    PlaceCategory.TAXI: "Такси",
    PlaceCategory.PARKING: "Парковка",
    PlaceCategory.OTHER: "Другое",
}

MAP_REPORT_LABELS = {
    ShopComplaintType.MAP_WRONG_HOURS: "Неверные часы работы",
    ShopComplaintType.MAP_WRONG_PHONE: "Неверный телефон",
    ShopComplaintType.MAP_CLOSED: "Заведение закрыто",
    ShopComplaintType.MAP_WRONG_ADDRESS: "Неверный адрес",
    ShopComplaintType.MAP_OTHER: "Другая ошибка на карте",
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
