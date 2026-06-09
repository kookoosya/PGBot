"""Map UI filter presets for the public map."""

from __future__ import annotations

from dataclasses import dataclass

from app.models.enums import PlaceCategory


@dataclass(frozen=True, slots=True)
class MapFilterMode:
    """Quick filter chip for the public map."""

    id: str
    label: str
    category: PlaceCategory | None = None
    shops_only: bool = False
    useful_only: bool = False
    show_taxi: bool = False


MAP_FILTER_MODES: tuple[MapFilterMode, ...] = (
    MapFilterMode(id="shops", label="🛒 Магазины", shops_only=True),
    MapFilterMode(id="pharmacy", label="💊 Аптеки", category=PlaceCategory.PHARMACY),
    MapFilterMode(id="taxi", label="🚕 Такси", show_taxi=True),
    MapFilterMode(id="useful", label="🏦 Полезное", useful_only=True),
    MapFilterMode(id="landmarks", label="🏛 Достопримечательности", category=PlaceCategory.CULTURE),
)


def get_map_filter_modes() -> list[dict[str, str | bool | None]]:
    """Return map quick-filter definitions for the frontend."""
    return [
        {
            "id": mode.id,
            "label": mode.label,
            "category": mode.category.value if mode.category else None,
            "shops_only": mode.shops_only,
            "useful_only": mode.useful_only,
            "show_taxi": mode.show_taxi,
        }
        for mode in MAP_FILTER_MODES
    ]
