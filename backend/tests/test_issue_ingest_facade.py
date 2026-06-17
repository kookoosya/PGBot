"""Smoke tests for issue ingest package exports."""

import app.services.issue as pkg
from app.services.issue import dedup as dedup_mod
from app.services.issue import gemini_analysis as gemini_mod
from app.services.issue import ingest as ingest_mod
from app.services.issue import residents as residents_mod


def test_package_exports_ingest():
    assert pkg.process_web_complaint is ingest_mod.process_web_complaint
    assert pkg.process_incoming_message is ingest_mod.process_incoming_message


def test_package_exports_residents():
    assert pkg.get_or_create_resident is residents_mod.get_or_create_resident
    assert pkg.get_or_create_web_resident is residents_mod.get_or_create_web_resident


def test_package_exports_dedup():
    assert pkg.should_link_duplicate_issue is dedup_mod.should_link_duplicate_issue
    assert pkg.find_similar_issues is dedup_mod.find_similar_issues


def test_package_gemini_export():
    assert pkg.run_gemini_with_retry is gemini_mod.run_gemini_with_retry
