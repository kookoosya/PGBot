from app.core.password_policy import validate_password


def test_rejects_short_password():
    ok, msg = validate_password("Ab1")
    assert not ok
    assert "10" in msg


def test_rejects_weak_password():
    ok, _ = validate_password("password123")
    assert not ok


def test_accepts_strong_password():
    ok, msg = validate_password("Pushkin2026!")
    assert ok
    assert msg == ""
