"""Готовые маршруты — остановки только из stage-02 inventory (verified coords)."""

MUSEUM_NAME = "Государственный музей-заповедник А. С. Пушкина «Михайловское»"
MONASTERY_NAME = "Свято-Успенский Святогорский мужской монастырь"

# stable_key: museum-mikhailovskoe-nkc
MUSEUM_STOP = {
    "name": MUSEUM_NAME,
    "address": "бульвар им. С. С. Гейченко, 1",
    "latitude": 57.0234195,
    "longitude": 28.9307908,
    "source": "pushkinland.ru",
}

# stable_key: monastery-svyatogorsky
MONASTERY_STOP = {
    "name": MONASTERY_NAME,
    "address": "ул. Пушкинская, 1",
    "latitude": 57.0224228,
    "longitude": 28.9200652,
    "source": "svyatogorskiy-monastery.ru",
}

# stable_key: pyaterochka-lenina-20a
PYATEROCHKA_STOP = {
    "name": "Пятёрочка",
    "address": "ул. Ленина, 20А",
    "latitude": 57.0264,
    "longitude": 28.9106,
    "source": "yandex.ru/maps/org/pyatyorochka/48515124540/",
}

# stable_key: kafe-pushkin-lenina-3
CAFE_PUSHKIN_STOP = {
    "name": "Кафе «Пушкинъ»",
    "address": "пл. Ленина, 3",
    "latitude": 57.0267,
    "longitude": 28.9112,
    "source": "yandex.ru/maps",
}

# stable_key: svyatogor-cafe-lenina-2
CAFE_SVYATOGOR_STOP = {
    "name": "Святогоръ",
    "address": "ул. Ленина, 2",
    "latitude": 57.0265,
    "longitude": 28.9115,
    "source": "2gis.ru/firm/70000001030949997",
}

# stable_key: sieszka-pushkinskaya-69
CAFE_SIESZKA_STOP = {
    "name": "Сиежка",
    "address": "ул. Пушкинская, 69",
    "latitude": 57.021324,
    "longitude": 28.915162,
    "source": "yandex.ru/maps/org/sieszka/171350854821/",
}

# stable_key: pushkin-park-lenina-42a
RESTAURANT_PARK_STOP = {
    "name": "Пушкин-Парк",
    "address": "ул. Ленина, 42А",
    "latitude": 57.0262,
    "longitude": 28.9115,
    "source": "2gis.ru/firm/70000001030949997",
}

# stable_key: avtovokzal-novorzhevskaya-30
BUS_STOP = {
    "name": "Автовокзал Пушкинские Горы",
    "address": "ул. Новоржевская, 30",
    "latitude": 57.0212461,
    "longitude": 28.9350885,
    "source": "openstreetmap.org",
}

# stable_key: parking-museum-kassa
PARKING_STOP = {
    "name": "Парковка у кассы музея",
    "address": "бульв. им. С. С. Гейченко, 1",
    "latitude": 57.0233,
    "longitude": 28.9308,
    "source": "pushkinland.ru",
}

# stable_key: usadba-mikhailovskoe-selo (NEARBY_ATTRACTION)
MIKHAILOVSKOE_ESTATE_STOP = {
    "name": "Усадьба «Михайловское»",
    "address": "с. Михайловское",
    "latitude": 57.054,
    "longitude": 28.968,
    "source": "pushkinland.ru",
}

# stable_key: parking-tri-sosen
PARKING_TRI_SOSEN_STOP = {
    "name": "Парковка «У Трёх Сосен»",
    "address": "у с. Михайловское",
    "latitude": 57.052,
    "longitude": 28.965,
    "source": "pushkinland.ru",
}

# stable_key: apteka-a-lenina-20a
PHARMACY_LENINA_20A_STOP = {
    "name": "Аптека-А",
    "address": "ул. Ленина, 20А",
    "latitude": 57.0263,
    "longitude": 28.9108,
    "source": "2gis.ru/firm/70000001046944968",
}

# stable_key: apteka-a-novorzhevskaya-25
PHARMACY_NOVORZHEVSKAYA_STOP = {
    "name": "Аптека-А",
    "address": "ул. Новоржевская, 25",
    "latitude": 57.0258,
    "longitude": 28.9125,
    "source": "yandex.ru/maps/org/apteka_a/193128665660/",
}

# stable_key: farm-m-lenina-42
PHARMACY_FARM_STOP = {
    "name": "Фарм-М",
    "address": "ул. Ленина, 42",
    "latitude": 57.0261,
    "longitude": 28.9112,
    "source": "yandex.ru/maps",
}

# stable_key: hospital-pushkinogorsky-filial
HOSPITAL_STOP = {
    "name": "Пушкиногорская межрайонная больница",
    "address": "ул. Ленина, 41",
    "latitude": 57.030632,
    "longitude": 28.932777,
    "source": "pushgori-crb.ru",
}

# stable_key: druzhba-hotel-lenina-8
HOTEL_DRUZHBA_STOP = {
    "name": "Дружба",
    "address": "ул. Ленина, 8",
    "latitude": 57.0263,
    "longitude": 28.911,
    "source": "yandex.ru/maps/org/druzhba/1077179086/",
}

# stable_key: usadba-trigorskaya-hotel
HOTEL_TRIGORSKAYA_STOP = {
    "name": "Усадьба Тригорская",
    "address": "ул. Тригорская, 1",
    "latitude": 57.0248,
    "longitude": 28.9045,
    "source": "trigorskaya1.ru",
}

# stable_key: dom-klassika-pushkinskaya-47
HOTEL_DOM_KLASSIKA_STOP = {
    "name": "Дом Классика",
    "address": "ул. Пушкинская, 47",
    "latitude": 57.0245,
    "longitude": 28.916,
    "source": "yandex.ru/maps",
}

# stable_key: turbaza-pushkinogorye
HOTEL_TURBAZA_STOP = {
    "name": "Пушкиногорье",
    "address": "микрорайон Турбаза",
    "latitude": 57.034788,
    "longitude": 28.925819,
    "source": "pgtur.ru",
}

# stable_key: mfc-lenina-6
MFC_STOP = {
    "name": "МФЦ «Мои документы»",
    "address": "ул. Ленина, 6",
    "latitude": 57.02541,
    "longitude": 28.928025,
    "source": "mfc.pskov.ru",
}

# stable_key: pochta-rossii-lenina-22
POST_STOP = {
    "name": "Почта России",
    "address": "ул. Ленина, 22",
    "latitude": 57.0266,
    "longitude": 28.9118,
    "source": "yandex.ru/maps",
}

# stable_key: sberbank-atm-lenina-40
BANK_STOP = {
    "name": "Сбербанк (банкомат)",
    "address": "ул. Ленина, 40",
    "latitude": 57.0264,
    "longitude": 28.9102,
    "source": "sberbank.ru",
}

# stable_key: kdc-sadovaya-1
KDC_STOP = {
    "name": "МБУК «Культурно-досуговый центр»",
    "address": "ул. Садовая, 1",
    "latitude": 57.020315,
    "longitude": 28.916176,
    "source": "kdc-pushgory.ru",
}

# stable_key: magnit-lenina-42
MAGNIT_STOP = {
    "name": "Магнит",
    "address": "ул. Ленина, 42",
    "latitude": 57.0261,
    "longitude": 28.9112,
    "source": "yandex.ru/maps",
}

TYRE_ROUTE_NAME = "Шиномонтаж"

VERIFIED_ROUTE_STOP_NAMES = frozenset(
    stop["name"]
    for stop in (
        MUSEUM_STOP,
        MONASTERY_STOP,
        PYATEROCHKA_STOP,
        CAFE_PUSHKIN_STOP,
        CAFE_SVYATOGOR_STOP,
        CAFE_SIESZKA_STOP,
        RESTAURANT_PARK_STOP,
        BUS_STOP,
        PARKING_STOP,
        MIKHAILOVSKOE_ESTATE_STOP,
        PARKING_TRI_SOSEN_STOP,
        PHARMACY_LENINA_20A_STOP,
        PHARMACY_NOVORZHEVSKAYA_STOP,
        PHARMACY_FARM_STOP,
        HOSPITAL_STOP,
        HOTEL_DRUZHBA_STOP,
        HOTEL_TRIGORSKAYA_STOP,
        HOTEL_DOM_KLASSIKA_STOP,
        HOTEL_TURBAZA_STOP,
        MFC_STOP,
        POST_STOP,
        BANK_STOP,
        KDC_STOP,
        MAGNIT_STOP,
    )
)

MAP_ROUTES: list[dict] = [
    {
        "id": "pushkin-classic",
        "title": "Классический Пушкин",
        "duration": "ориентировочно 3–4 ч",
        "description": "Музей-заповедник, монастырь и парковка у кассы",
        "stops": [MUSEUM_STOP, MONASTERY_STOP, PARKING_STOP],
    },
    {
        "id": "pushkin-estate-day",
        "title": "Михайловское: день на усадьбе",
        "duration": "ориентировочно 5–6 ч",
        "description": "Касса музея → усадьба → парковка у Трёх Сосен → монастырь",
        "stops": [PARKING_STOP, MUSEUM_STOP, MIKHAILOVSKOE_ESTATE_STOP, PARKING_TRI_SOSEN_STOP, MONASTERY_STOP],
    },
    {
        "id": "pilgrim",
        "title": "Паломнический",
        "duration": "ориентировочно 2–3 ч",
        "description": "Святогорский монастырь и музей-заповедник",
        "stops": [MONASTERY_STOP, MUSEUM_STOP],
    },
    {
        "id": "village-evening",
        "title": "Вечерний посёлок",
        "duration": "ориентировочно 2–3 ч",
        "description": "Монастырь → центр → кафе",
        "stops": [MONASTERY_STOP, CAFE_PUSHKIN_STOP, PYATEROCHKA_STOP],
    },
    {
        "id": "village-services",
        "title": "Посёлок: бытовой маршрут",
        "duration": "ориентировочно 1–2 ч",
        "description": "Автовокзал, магазин и кафе в центре посёлка",
        "stops": [BUS_STOP, PYATEROCHKA_STOP, CAFE_PUSHKIN_STOP],
    },
    {
        "id": "from-bus",
        "title": "Приехал на автобусе",
        "duration": "ориентировочно 4–6 ч",
        "description": "Автовокзал → касса музея → усадьба Михайловское",
        "stops": [BUS_STOP, MUSEUM_STOP, MIKHAILOVSKOE_ESTATE_STOP],
    },
    {
        "id": "village-food",
        "title": "Где поесть в посёлке",
        "duration": "ориентировочно 1–2 ч",
        "description": "Кафе и столовые в центре и на Пушкинской",
        "stops": [CAFE_PUSHKIN_STOP, CAFE_SVYATOGOR_STOP, CAFE_SIESZKA_STOP, RESTAURANT_PARK_STOP],
    },
    {
        "id": "village-hotels",
        "title": "Где остановиться",
        "duration": "ориентировочно 30 мин",
        "description": "Гостиницы и турбаза — проверенные адреса",
        "stops": [HOTEL_DRUZHBA_STOP, HOTEL_TRIGORSKAYA_STOP, HOTEL_DOM_KLASSIKA_STOP, HOTEL_TURBAZA_STOP],
    },
    {
        "id": "pharmacy-health",
        "title": "Аптеки и медицина",
        "duration": "ориентировочно 1 ч",
        "description": "Аптеки в центре и больница",
        "stops": [PHARMACY_LENINA_20A_STOP, PHARMACY_NOVORZHEVSKAYA_STOP, PHARMACY_FARM_STOP, HOSPITAL_STOP],
    },
    {
        "id": "public-services",
        "title": "Полезное в посёлке",
        "duration": "ориентировочно 1 ч",
        "description": "МФЦ, почта, банкомат и магазины",
        "stops": [MFC_STOP, POST_STOP, BANK_STOP, MAGNIT_STOP, PYATEROCHKA_STOP],
    },
    {
        "id": "culture-kdc",
        "title": "Культура и КДЦ",
        "duration": "ориентировочно 2 ч",
        "description": "КДЦ, музей-заповедник и монастырь",
        "stops": [KDC_STOP, MUSEUM_STOP, MONASTERY_STOP],
    },
]


def get_map_routes() -> list[dict]:
    return MAP_ROUTES


def route_stop_names() -> set[str]:
    return {stop["name"] for route in MAP_ROUTES for stop in route["stops"]}
