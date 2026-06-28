"""Unit tests for classified content quality checks."""

from app.services.classified_antifraud import evaluate_classified_content


def test_evaluate_classified_content_accepts_normal_ad():
    assert evaluate_classified_content("Дрова берёзовые", "Сухие дрова, самовывоз у НКЦ") is None


def test_evaluate_classified_content_rejects_short_description():
    assert evaluate_classified_content("Дрова", "Сухие") is not None


def test_evaluate_classified_content_rejects_all_caps_title():
    err = evaluate_classified_content("ПРОДАМ ДРОВА СРОЧНО ДЁШЕВО", "Сухие дрова, самовывоз у НКЦ в посёлке")
    assert err is not None
