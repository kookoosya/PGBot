from app.services.classified_antifraud import find_scam_phrase, normalize_phone, validate_phone


def test_normalize_phone_from_8_prefix():
    assert normalize_phone("8 (911) 123-45-67") == "79111234567"


def test_validate_phone_rejects_bad_prefix():
    assert validate_phone("+71234567890") is not None


def test_find_scam_phrase():
    assert find_scam_phrase("Нужен аванс 100%") == "аванс"
