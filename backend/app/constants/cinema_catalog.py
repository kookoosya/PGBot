"""Known film titles for VK/cinema post parsing (normalized keys → metadata)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FilmMetadata:
    title: str
    genre: str
    teaser: str


# Keys are lowercase normalized titles for fuzzy lookup.
FILM_CATALOG: dict[str, FilmMetadata] = {
    "граф монте-кристо": FilmMetadata(
        title="Граф Монте-Кристо",
        genre="Приключения",
        teaser="Экранизация романа Дюма — история мести, свободы и приключений на фоне Средиземноморья.",
    ),
    "дюна: часть вторая": FilmMetadata(
        title="Дюна: Часть вторая",
        genre="Фантастика",
        teaser="Пол Атрейдес продолжает путь на Арракисе в масштабной космической саге.",
    ),
    "дюна 2": FilmMetadata(
        title="Дюна: Часть вторая",
        genre="Фантастика",
        teaser="Пол Атрейдес продолжает путь на Арракисе в масштабной космической саге.",
    ),
    "подай знак": FilmMetadata(
        title="Подай знак",
        genre="Триллер",
        teaser="Напряжённый триллер о поисках пропавшей девочки в лесах Миннесоты.",
    ),
    "кунг-фу панда 4": FilmMetadata(
        title="Кунг-фу Панда 4",
        genre="Мультфильм",
        teaser="По возвращении к мирной жизни По встречает нового соперника и учится быть наставником.",
    ),
    "годзилла и конг: новая империя": FilmMetadata(
        title="Годзилла и Конг: Новая империя",
        genre="Фантастика",
        teaser="Титаны сталкиваются с невиданной угрозой из скрытого мира Земли.",
    ),
    "плохие парни 2": FilmMetadata(
        title="Плохие парни 2",
        genre="Комедия",
        teaser="Команда антигероев снова в деле — остроумное продолжение анимационного хита.",
    ),
    "челюсти 50": FilmMetadata(
        title="Челюсти 50",
        genre="Триллер",
        teaser="Юбилейное возвращение культовой истории об охоте на акулу у побережья.",
    ),
    "внутри убийцы": FilmMetadata(
        title="Внутри убийцы",
        genre="Детектив",
        teaser="Детектив расследует серию загадочных преступлений с неожиданным финалом.",
    ),
    "поток": FilmMetadata(
        title="Поток",
        genre="Мультфильм",
        teaser="Безмолвная анимация о коте и псе, переживающих потоп в родном доме.",
    ),
    "битва за битвой": FilmMetadata(
        title="Битва за битвой",
        genre="Боевик",
        teaser="Группа наёмников втягивается в опасную игру с высокими ставками.",
    ),
    "снегирь": FilmMetadata(
        title="Снегирь",
        genre="Драма",
        teaser="История любви и выбора на фоне исторических событий начала XX века.",
    ),
    "айда": FilmMetadata(
        title="Айда",
        genre="Драма",
        teaser="Драматическая экранизация о судьбе женщины во время трагических событий на Балканах.",
    ),
}

GENERIC_CINEMA_TITLES: frozenset[str] = frozenset({
    "кино",
    "кино в пскове",
    "киноафиша",
    "афиша",
    "афиша кино",
    "премьера",
    "премьера недели",
    "новинки кино",
    "новинки проката",
    "в прокате",
    "сеанс",
    "сеансы",
    "кинотеатр",
    "кинопоказ",
    "кино на выходных",
    "событие",
})


def _normalize_key(value: str) -> str:
    return " ".join(value.lower().replace("«", "").replace("»", "").replace('"', "").split())


def lookup_film(text: str) -> FilmMetadata | None:
    """Find catalog entry by title fragment or full post text."""
    if not text:
        return None
    normalized = _normalize_key(text)
    if normalized in FILM_CATALOG:
        return FILM_CATALOG[normalized]
    for key, meta in FILM_CATALOG.items():
        if key in normalized or _normalize_key(meta.title) in normalized:
            return meta
    return None


def is_generic_cinema_title(title: str) -> bool:
    normalized = _normalize_key(title)
    if normalized in GENERIC_CINEMA_TITLES:
        return True
    return any(
        phrase in normalized
        for phrase in ("премьера недели", "кино в ", "новинки ", "в прокате")
    )
