"""Smoke tests for issue_processor facade after ingest package split."""

import app.services.issue_processor as facade
from app.services.issue import dedup as dedup_mod
from app.services.issue import gemini_analysis as gemini_mod
from app.services.issue import ingest as ingest_mod
from app.services.issue import residents as residents_mod


def test_facade_exports_ingest():
    assert facade.process_web_complaint is ingest_mod.process_web_complaint
    assert facade.process_incoming_message is ingest_mod.process_incoming_message


def test_facade_exports_residents():
    assert facade.get_or_create_resident is residents_mod.get_or_create_resident
    assert facade.get_or_create_web_resident is residents_mod.get_or_create_web_resident


def test_facade_exports_dedup():
    assert facade.should_link_duplicate_issue is dedup_mod.should_link_duplicate_issue
    assert facade.find_similar_issues is dedup_mod.find_similar_issues


def test_facade_gemini_alias():
    assert facade._run_gemini_with_retry is gemini_mod.run_gemini_with_retry
