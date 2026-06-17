"""Smoke tests for event package public exports."""

import app.services.event as pkg
from app.services.event import admin as admin_mod
from app.services.event import mappers as mappers_mod
from app.services.event import public as public_mod


def test_package_exports_admin_functions():
    assert pkg.create_event is admin_mod.create_event
    assert pkg.update_event is admin_mod.update_event
    assert pkg.list_events_admin is admin_mod.list_events_admin


def test_package_exports_public_functions():
    assert pkg.get_upcoming_events is public_mod.get_upcoming_events
    assert pkg.search_public_events is public_mod.search_public_events


def test_package_exports_mappers():
    assert pkg.event_to_response is mappers_mod.event_to_response
    assert pkg.event_category_label is mappers_mod.event_category_label


def test_package_schema_types():
    assert pkg.EventValidationError is not None
    assert pkg.EventCreateInput is not None
