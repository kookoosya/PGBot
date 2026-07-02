"""Готовые туристические маршруты — только точки, подтверждённые на этапе 1."""

MUSEUM_NAME = "Государственный музей-заповедник А. С. Пушкина «Михайловское»"
MONASTERY_NAME = "Свято-Успенский Святогорский мужской монастырь"

MUSEUM_STOP = {
    "name": MUSEUM_NAME,
    "address": "бульвар им. С. С. Гейченко, 1",
    "latitude": 57.0234195,
    "longitude": 28.9307908,
}

MONASTERY_STOP = {
    "name": MONASTERY_NAME,
    "address": "ул. Пушкинская, 1",
    "latitude": 57.0224228,
    "longitude": 28.9200652,
}

VERIFIED_ROUTE_STOP_NAMES = frozenset({MUSEUM_NAME, MONASTERY_NAME})

MAP_ROUTES: list[dict] = [
    {
        "id": "pushkin-classic",
        "title": "Классический Пушкин",
        "duration": "—",
        "description": "Музей-заповедник и Святогорский монастырь",
        "stops": [
            MUSEUM_STOP,
            MONASTERY_STOP,
        ],
    },
    {
        "id": "pilgrim",
        "title": "Паломнический",
        "duration": "—",
        "description": "Святогорский монастырь и музей-заповедник",
        "stops": [
            MONASTERY_STOP,
            MUSEUM_STOP,
        ],
    },
]


def get_map_routes() -> list[dict]:
    return MAP_ROUTES
