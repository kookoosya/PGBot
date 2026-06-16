"""Smoke tests for event_service facade after package split."""

import app.services.event_service as facade
from app.services.event import admin as admin_mod
from app.services.event import mappers as mappers_mod
from app.services.event import public as public_mod


def test_facade_exports_public():
    assert facade.get_upcoming_events is public_mod.get_upcoming_events
    assert facade.search_public_events is public_mod.search_public_events
    assert facade.get_public_event_by_id is public_mod.get_public_event_by_id


def test_facade_exports_admin():
    assert facade.create_event is admin_mod.create_event
    assert facade.update_event is admin_mod.update_event
    assert facade.list_events_admin is admin_mod.list_events_admin


def test_facade_exports_mappers():
    assert facade.event_to_response is mappers_mod.event_to_response
    assert facade.event_category_label is mappers_mod.event_category_label
    assert facade.build_event_list_response is mappers_mod.build_event_list_response


def test_facade_schema_types():
    assert facade.EventNotFoundError is not None
    assert facade.EventValidationError is not None
