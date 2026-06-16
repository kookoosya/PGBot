import enum


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
