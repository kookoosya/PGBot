"""Smoke tests for verification package public exports."""

import app.services.verification as pkg
from app.services.verification import moderation as moderation_mod
from app.services.verification import register as register_mod
from app.services.verification import responses as responses_mod


def test_package_exports_register():
    assert pkg.register_organization is register_mod.register_organization
    assert pkg.register_official is register_mod.register_official


def test_package_exports_moderation():
    assert pkg.list_pending_verifications is moderation_mod.list_pending_verifications
    assert pkg.approve_verification is moderation_mod.approve_verification
    assert pkg.reject_verification is moderation_mod.reject_verification


def test_package_exports_response_mapper():
    assert pkg.verification_to_response is responses_mod.verification_to_response


def test_package_schema_types():
    assert pkg.VerificationNotFoundError is not None
    assert pkg.VerificationValidationError is not None
