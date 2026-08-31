import pytest
from pydantic import ValidationError

from codebase_os.config import Settings, get_settings, validate_settings


def test_settings_read_environment(monkeypatch):
    monkeypatch.setenv("CODEBASEOS_ENVIRONMENT", "test")
    monkeypatch.setenv("CODEBASEOS_RETENTION_DAYS", "30")
    settings = Settings.from_env()
    assert settings.environment == "test"
    assert settings.retention_days == 30
    assert settings.model_api_key is None


def test_production_rejects_sqlite(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("CODEBASEOS_ENVIRONMENT", "production")
    monkeypatch.setenv("CODEBASEOS_DATABASE_URL", "sqlite:///local.db")
    with pytest.raises(ValidationError):
        validate_settings()
    get_settings.cache_clear()

