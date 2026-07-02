"""Готовые туристические маршруты — точки из stage-02 inventory."""

MUSEUM_NAME = "Государственный музей-заповедник А. С. Пушкина «Михайловское»"
MONASTERY_NAME = "Свято-Успенский Святогорский мужской монастырь"

MUSEUM_STOP = {
    "name": MUSEUM_NAME,
    "address": "бульвар им. С. С. Гейченко, 1",
    "latitude": 57.0234195,
    "longitude": 28.9307908,
    "source": "pushkinland.ru",
}

MONASTERY_STOP = {
    "name": MONASTERY_NAME,
    "address": "ул. Пушкинская, 1",
    "latitude": 57.0224228,
    "longitude": 28.9200652,
    "source": "svyatogorskiy-monastery.ru",
}

PYATEROCHKA_STOP = {
    "name": "Пятёрочка",
    "address": "ул. Ленина, 20А",
    "latitude": 57.0264,
    "longitude": 28.9106,
    "source": "yandex.ru/maps/org/pyatyorochka/48515124540/",
}

CAFE_STOP = {
    "name": "Кафе «Пушкинъ»",
    "address": "пл. Ленина, 3",
    "latitude": 57.0267,
    "longitude": 28.9112,
    "source": "yandex.ru/maps",
}

BUS_STOP = {
    "name": "Автовокзал Пушкинские Горы",
    "address": "ул. Новоржевская, 30",
    "latitude": 57.0212461,
    "longitude": 28.9350885,
    "source": "openstreetmap.org",
}

TYRE_STOP = {
    "name": "Шиномонтаж",
    "address": "ул. Аэродромная, 23",
    "latitude": 57.0173,
    "longitude": 28.9335,
    "source": "OWNER_CONFIRMED",
}

PARKING_STOP = {
    "name": "Парковка у кассы музея",
    "address": "бульв. им. С. С. Гейченко, 1",
    "latitude": 57.0233,
    "longitude": 28.9308,
    "source": "pushkinland.ru",
}

VERIFIED_ROUTE_STOP_NAMES = frozenset(
    stop["name"]
    for stop in (
        MUSEUM_STOP,
        MONASTERY_STOP,
        PYATEROCHKA_STOP,
        CAFE_STOP,
        BUS_STOP,
        TYRE_STOP,
        PARKING_STOP,
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
        "id": "pilgrim",
        "title": "Паломнический",
        "duration": "ориентировочно 2–3 ч",
        "description": "Святогорский монастырь и музей-заповедник",
        "stops": [MONASTERY_STOP, MUSEUM_STOP],
    },
    {
        "id": "village-services",
        "title": "Посёлок: бытовой маршрут",
        "duration": "ориентировочно 1–2 ч",
        "description": "Автовокзал, магазин и кафе в центре посёлка",
        "stops": [BUS_STOP, PYATEROCHKA_STOP, CAFE_STOP],
    },
    {
        "id": "auto-aerodromnaya",
        "title": "Авто: шиномонтаж",
        "duration": "ориентировочно 30 мин",
        "description": "Шиномонтаж на ул. Аэродромной — подтверждено владельцем",
        "stops": [TYRE_STOP],
    },
]


def get_map_routes() -> list[dict]:
    return MAP_ROUTES
