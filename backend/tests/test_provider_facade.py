"""Smoke tests for provider package public exports."""

import app.services.provider as pkg
from app.services.provider import booking as booking_mod
from app.services.provider import cabinet as cabinet_mod
from app.services.provider import register as register_mod
from app.services.provider import search as search_mod


def test_package_exports_booking():
    assert pkg.book_appointment is booking_mod.book_appointment
    assert pkg.get_provider_slots_response is booking_mod.get_provider_slots_response


def test_package_exports_register():
    assert pkg.register_provider is register_mod.register_provider


def test_package_exports_search():
    assert pkg.search_providers is search_mod.search_providers
    assert pkg.get_provider_details is search_mod.get_provider_details


def test_package_exports_cabinet():
    assert pkg.add_busy_block is cabinet_mod.add_busy_block
    assert pkg.list_busy_blocks is cabinet_mod.list_busy_blocks


def test_package_schema_types():
    assert pkg.ProviderValidationError is not None
