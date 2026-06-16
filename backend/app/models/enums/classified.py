import enum


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
    NEIGHBOR_HELP = "neighbor_help"
    OTHER = "other"


NEIGHBOR_HELP_CATEGORIES = {
    ClassifiedCategory.NEIGHBOR_HELP,
}

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
    ClassifiedCategory.NEIGHBOR_HELP: "Сосед помогает",
    ClassifiedCategory.OTHER: "Другое",
}
