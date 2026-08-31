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


def test_settings_maps_online_integration_configuration(monkeypatch):
    values = {
        "CODEBASEOS_GITHUB_CLIENT_ID": "github-client",
        "CODEBASEOS_GITHUB_CLIENT_SECRET": "github-secret",
        "CODEBASEOS_GITHUB_CALLBACK_URL": "https://app.example/auth/github/callback",
        "CODEBASEOS_MODEL_NAME": "reasoning-model",
        "CODEBASEOS_MODEL_BASE_URL": "https://models.example/v1",
        "CODEBASEOS_OBJECT_STORAGE_PROVIDER": "s3",
        "CODEBASEOS_OBJECT_STORAGE_BUCKET": "snapshots",
        "CODEBASEOS_OBJECT_STORAGE_ENDPOINT": "https://objects.example",
        "CODEBASEOS_AUTH_PROVIDER": "github",
        "CODEBASEOS_SESSION_SECRET": "long-session-secret",
    }
    for key, value in values.items():
        monkeypatch.setenv(key, value)

    settings = Settings.from_env()

    assert settings.github_client_id == "github-client"
    assert settings.github_callback_url == values["CODEBASEOS_GITHUB_CALLBACK_URL"]
    assert settings.model_name == "reasoning-model"
    assert settings.model_base_url == values["CODEBASEOS_MODEL_BASE_URL"]
    assert settings.object_storage_provider == "s3"
    assert settings.object_storage_bucket == "snapshots"
    assert settings.auth_provider == "github"
    assert settings.session_secret.get_secret_value() == "long-session-secret"
    monkeypatch.setenv("CODEBASEOS_ENVIRONMENT", "production")
    monkeypatch.setenv("CODEBASEOS_DATABASE_URL", "sqlite:///local.db")
    with pytest.raises(ValidationError):
        validate_settings()
    get_settings.cache_clear()
