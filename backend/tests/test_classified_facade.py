"""Smoke tests for classified_service facade after package split."""

import app.services.classified_service as facade
from app.services.classified import create as create_mod
from app.services.classified import moderation as moderation_mod
from app.services.classified import search as search_mod


def test_facade_exports_create_functions():
    assert facade.create_classified_ad is create_mod.create_classified_ad
    assert facade.create_classified_ad_from_vk is create_mod.create_classified_ad_from_vk


def test_facade_exports_search_functions():
    assert facade.search_classifieds is search_mod.search_classifieds
    assert facade.increment_ad_views is search_mod.increment_ad_views


def test_facade_exports_moderation():
    assert facade.moderate_classified_ad is moderation_mod.moderate_classified_ad


def test_facade_schema_types():
    assert facade.ClassifiedValidationError is not None
    assert facade.ClassifiedCreateInput is not None
