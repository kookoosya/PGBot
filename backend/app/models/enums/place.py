import enum


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
    VET = "vet"
    GOVERNMENT = "government"
    TRANSPORT = "transport"
    CULTURE = "culture"
    HOTEL = "hotel"
    RENTAL = "rental"
    GAS = "gas"
    BEAUTY = "beauty"
    TYRE = "tyre"
    AUTO = "auto"
    CAR_WASH = "car_wash"
    AUTO_PARTS = "auto_parts"
    TOWING = "towing"
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
    PlaceCategory.VET: "Ветеринария",
    PlaceCategory.GOVERNMENT: "Госучреждение",
    PlaceCategory.TRANSPORT: "Транспорт",
    PlaceCategory.CULTURE: "Культура",
    PlaceCategory.HOTEL: "Гостиница",
    PlaceCategory.RENTAL: "Посуточно",
    PlaceCategory.GAS: "АЗС",
    PlaceCategory.BEAUTY: "Красота/услуги",
    PlaceCategory.TYRE: "Шиномонтаж",
    PlaceCategory.AUTO: "Автосервис",
    PlaceCategory.CAR_WASH: "Автомойка",
    PlaceCategory.AUTO_PARTS: "Автозапчасти",
    PlaceCategory.TOWING: "Эвакуатор",
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
