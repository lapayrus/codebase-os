from functools import lru_cache
import os

from pydantic import BaseModel, Field, SecretStr, ValidationError, field_validator


class Settings(BaseModel):
    environment: str = "development"
    database_url: str = "sqlite:///./codebaseos.db"
    github_app_id: str | None = None
    github_private_key: SecretStr | None = None
    github_webhook_secret: SecretStr | None = None
    model_provider: str = "none"
    model_api_key: SecretStr | None = None
    max_file_bytes: int = Field(default=1_000_000, ge=1_024, le=50_000_000)
    retention_days: int = Field(default=90, ge=1, le=3_650)

    @field_validator("environment", "model_provider")
    @classmethod
    def non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("value must not be empty")
        return value.strip().lower()

    @classmethod
    def from_env(cls) -> "Settings":
        values = {
            "environment": os.getenv("CODEBASEOS_ENVIRONMENT", "development"),
            "database_url": os.getenv("CODEBASEOS_DATABASE_URL", "sqlite:///./codebaseos.db"),
            "github_app_id": os.getenv("CODEBASEOS_GITHUB_APP_ID"),
            "github_private_key": os.getenv("CODEBASEOS_GITHUB_PRIVATE_KEY"),
            "github_webhook_secret": os.getenv("CODEBASEOS_GITHUB_WEBHOOK_SECRET"),
            "model_provider": os.getenv("CODEBASEOS_MODEL_PROVIDER", "none"),
            "model_api_key": os.getenv("CODEBASEOS_MODEL_API_KEY"),
            "max_file_bytes": os.getenv("CODEBASEOS_MAX_FILE_BYTES", "1000000"),
            "retention_days": os.getenv("CODEBASEOS_RETENTION_DAYS", "90"),
        }
        return cls.model_validate(values)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings.from_env()


def validate_settings() -> Settings:
    settings = get_settings()
    if settings.environment == "production" and settings.database_url.startswith("sqlite"):
        raise ValidationError.from_exception_data(
            title="Settings",
            line_errors=[{"type": "value_error", "loc": ("database_url",), "input": settings.database_url,
                         "ctx": {"error": "production requires a durable database URL"}}],
        )
    return settings

