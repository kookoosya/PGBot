"""Кинотеатры Пскова — для подстановки места и парсинга афиш."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PskovCinema:
    name: str
    address: str
    aliases: tuple[str, ...]


PSKOV_CINEMAS: tuple[PskovCinema, ...] = (
    PskovCinema(
        name='Кинотеатр «Победа»',
        address="Октябрьский пр., 17",
        aliases=("победа", "pobeda", "кинотеатр победа"),
    ),
    PskovCinema(
        name='Кинотеатр «Смена»',
        address="Октябрьский пр., 17а",
        aliases=("смена", "smena"),
    ),
    PskovCinema(
        name="Мираж Синема",
        address="ТРЦ «Акваполис», ул. Кузбасской Дивизии, 19",
        aliases=("мираж", "mirage", "акваполис", "mirazh"),
    ),
    PskovCinema(
        name="Silver Cinema",
        address="ТДЦ Fjord Plaza, д. Борисовичи, ул. Завеличенская, 23",
        aliases=("silver", "fjord", "сильвер", "борисовичи"),
    ),
    PskovCinema(
        name="Кинозал КДЦ",
        address="Пушкинские Горы, культурно-досуговый центр",
        aliases=("кдз", "кдц", "пушкинские горы", "пушкиногор"),
    ),
)


def match_pskov_cinema(text: str) -> PskovCinema | None:
    """Return cinema if ``text`` mentions a known venue."""
    if not text:
        return None
    lower = text.lower()
    for cinema in PSKOV_CINEMAS:
        if any(alias in lower for alias in cinema.aliases):
            return cinema
        if cinema.name.lower() in lower:
            return cinema
    return None


def format_cinema_location(text: str | None) -> str | None:
    """Build a readable location line from free text or cinema catalog."""
    if not text:
        return None
    cinema = match_pskov_cinema(text)
    if cinema:
        return f"{cinema.name}, {cinema.address}"
    return text.strip() or None
