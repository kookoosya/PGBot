"""Smoke tests for provider_service facade after package split."""

import app.services.provider_service as facade
from app.services.provider import booking as booking_mod
from app.services.provider import cabinet as cabinet_mod
from app.services.provider import moderation as moderation_mod
from app.services.provider import register as register_mod
from app.services.provider import search as search_mod


def test_facade_exports_register():
    assert facade.register_provider is register_mod.register_provider


def test_facade_exports_search():
    assert facade.search_providers is search_mod.search_providers
    assert facade.get_provider_details is search_mod.get_provider_details
    assert facade.list_pending_providers is search_mod.list_pending_providers


def test_facade_exports_booking():
    assert facade.book_appointment is booking_mod.book_appointment
    assert facade.get_provider_slots_response is booking_mod.get_provider_slots_response


def test_facade_exports_moderation():
    assert facade.approve_provider is moderation_mod.approve_provider
    assert facade.reject_provider is moderation_mod.reject_provider


def test_facade_exports_cabinet():
    assert facade.add_busy_block is cabinet_mod.add_busy_block
    assert facade.list_provider_appointments is cabinet_mod.list_provider_appointments


def test_facade_schema_types():
    assert facade.ProviderNotFoundError is not None
    assert facade.ProviderValidationError is not None
