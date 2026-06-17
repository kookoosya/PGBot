"""Smoke tests for weather package public exports."""

import app.services.weather as pkg
from app.services.weather import fetch as fetch_mod
from app.services.weather import format as format_mod


def test_package_exports_fetch():
    assert pkg.get_weather is fetch_mod.get_weather
    assert pkg.refresh_weather_cache is fetch_mod.refresh_weather_cache


def test_package_exports_format():
    assert pkg.format_weather_digest_lines is format_mod.format_weather_digest_lines
    assert pkg.format_weather_vk_current is format_mod.format_weather_vk_current


def test_package_schema_types():
    assert pkg.WeatherFetchError is not None
    assert pkg.WeatherSnapshot is not None
