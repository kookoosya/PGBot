"""Tests for VK Mini App launch-params verification."""

import base64
import hashlib
import hmac

from app.services.vk.mini_app_auth import parse_launch_params, verify_launch_sign, vk_mini_app_configured


def _sign_params(params: dict[str, str], secret: str) -> dict[str, str]:
    signed = dict(params)
    pairs = [f"{key}={signed[key]}" for key in sorted(signed.keys()) if key.startswith("vk_")]
    digest = hmac.new(secret.encode(), "&".join(pairs).encode(), hashlib.sha256).digest()
    signed["sign"] = base64.urlsafe_b64encode(digest).decode().rstrip("=")
    return signed


def test_parse_launch_params_strips_hash_and_question():
    raw = "#vk_user_id=42&vk_platform=desktop_web&sign=abc"
    parsed = parse_launch_params(raw)
    assert parsed["vk_user_id"] == "42"
    assert parsed["vk_platform"] == "desktop_web"


def test_verify_launch_sign_accepts_valid_signature():
    secret = "test-secret"
    params = _sign_params({"vk_user_id": "99", "vk_app_id": "123"}, secret)
    assert verify_launch_sign(params, secret) is True


def test_verify_launch_sign_rejects_tampered_params():
    secret = "test-secret"
    params = _sign_params({"vk_user_id": "99"}, secret)
    params["vk_user_id"] = "100"
    assert verify_launch_sign(params, secret) is False


def test_vk_mini_app_configured_false_without_env(monkeypatch):
    monkeypatch.setenv("VK_APP_ID", "")
    monkeypatch.setenv("VK_APP_SECRET", "")
    from app.config import get_settings

    get_settings.cache_clear()
    assert vk_mini_app_configured() is False
    get_settings.cache_clear()
