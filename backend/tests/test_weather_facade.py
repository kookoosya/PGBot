"""Smoke tests for weather_service facade."""

import app.services.weather_service as facade
from app.services.weather import fetch as fetch_mod
from app.services.weather import format as format_mod


def test_facade_exports_get_weather():
    assert facade.get_weather is fetch_mod.get_weather


def test_facade_exports_formatters():
    assert facade.format_weather_vk_current is format_mod.format_weather_vk_current
    assert facade.looks_like_hourly_weather is format_mod.looks_like_hourly_weather
