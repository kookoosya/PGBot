"""Smoke tests for classified package public exports."""

import app.services.classified as pkg
from app.services.classified import create as create_mod
from app.services.classified import moderation as moderation_mod
from app.services.classified import search as search_mod


def test_package_exports_create_functions():
    assert pkg.create_classified_ad is create_mod.create_classified_ad
    assert pkg.create_classified_ad_from_vk is create_mod.create_classified_ad_from_vk


def test_package_exports_search_functions():
    assert pkg.search_classifieds is search_mod.search_classifieds
    assert pkg.increment_ad_views is search_mod.increment_ad_views


def test_package_exports_moderation():
    assert pkg.moderate_classified_ad is moderation_mod.moderate_classified_ad


def test_package_schema_types():
    assert pkg.ClassifiedValidationError is not None
    assert pkg.ClassifiedCreateInput is not None
