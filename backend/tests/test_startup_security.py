import pytest
from app.config import Settings
from app.core.startup import validate_security_config


def test_production_rejects_default_secret():
    settings = Settings(DEBUG=False, SECRET_KEY="change-me-in-production-use-long-random-string")
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        validate_security_config(settings)


def test_vk_requires_secret():
    settings = Settings(DEBUG=True, VK_GROUP_TOKEN="token", VK_SECRET_KEY="")
    with pytest.raises(RuntimeError, match="VK_SECRET_KEY"):
        validate_security_config(settings)
