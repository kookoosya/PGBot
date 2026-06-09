from app.services.ai_chat import make_identifier


def test_make_identifier_vk():
    assert make_identifier(None, None, vk_id=12345) == "vk:12345"


def test_make_identifier_web_is_stable():
    a = make_identifier("1.2.3.4", "Mozilla")
    b = make_identifier("1.2.3.4", "Mozilla")
    assert a == b
    assert a.startswith("web:")
