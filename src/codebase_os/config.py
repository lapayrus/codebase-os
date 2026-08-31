from functools import lru_cache
import os

from pydantic import BaseModel, Field, SecretStr, ValidationError, field_validator


class Settings(BaseModel):
    environment: str = "development"
    database_url: str = "sqlite:///./codebaseos.db"
    supabase_url: str | None = None
    supabase_project_id: str | None = None
    supabase_publishable_key: SecretStr | None = None
    github_app_id: str | None = None
    github_private_key: SecretStr | None = None
    github_webhook_secret: SecretStr | None = None
    github_client_id: str | None = None
    github_client_secret: SecretStr | None = None
    github_callback_url: str | None = None
    github_api_url: str = "https://api.github.com"
    github_request_timeout: float = Field(default=15.0, gt=0, le=120)
    github_retry_count: int = Field(default=2, ge=0, le=5)
    model_provider: str = "none"
    model_api_key: SecretStr | None = None
    model_name: str | None = None
    model_base_url: str | None = None
    object_storage_provider: str = "local"
    object_storage_bucket: str = "codebaseos-snapshots"
    object_storage_endpoint: str | None = None
    object_storage_access_key: SecretStr | None = None
    object_storage_secret_key: SecretStr | None = None
    auth_provider: str = "github"
    session_secret: SecretStr | None = None
    supabase_jwt_secret: SecretStr | None = None
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
            "supabase_url": os.getenv("CODEBASEOS_SUPABASE_URL"),
            "supabase_project_id": os.getenv("CODEBASEOS_SUPABASE_PROJECT_ID"),
            "supabase_publishable_key": os.getenv("CODEBASEOS_SUPABASE_PUBLISHABLE_KEY"),
            "github_app_id": os.getenv("CODEBASEOS_GITHUB_APP_ID"),
            "github_private_key": os.getenv("CODEBASEOS_GITHUB_PRIVATE_KEY"),
            "github_webhook_secret": os.getenv("CODEBASEOS_GITHUB_WEBHOOK_SECRET"),
            "github_client_id": os.getenv("CODEBASEOS_GITHUB_CLIENT_ID"),
            "github_client_secret": os.getenv("CODEBASEOS_GITHUB_CLIENT_SECRET"),
            "github_callback_url": os.getenv("CODEBASEOS_GITHUB_CALLBACK_URL"),
        "github_api_url": os.getenv("CODEBASEOS_GITHUB_API_URL", "https://api.github.com"),
        "github_request_timeout": float(os.getenv("CODEBASEOS_GITHUB_REQUEST_TIMEOUT", "15")),
        "github_retry_count": int(os.getenv("CODEBASEOS_GITHUB_RETRY_COUNT", "2")),
            "model_provider": os.getenv("CODEBASEOS_MODEL_PROVIDER", "none"),
            "model_api_key": os.getenv("CODEBASEOS_MODEL_API_KEY"),
            "model_name": os.getenv("CODEBASEOS_MODEL_NAME"),
            "model_base_url": os.getenv("CODEBASEOS_MODEL_BASE_URL"),
            "object_storage_provider": os.getenv("CODEBASEOS_OBJECT_STORAGE_PROVIDER", "local"),
            "object_storage_bucket": os.getenv("CODEBASEOS_OBJECT_STORAGE_BUCKET", "codebaseos-snapshots"),
            "object_storage_endpoint": os.getenv("CODEBASEOS_OBJECT_STORAGE_ENDPOINT"),
            "object_storage_access_key": os.getenv("CODEBASEOS_OBJECT_STORAGE_ACCESS_KEY"),
            "object_storage_secret_key": os.getenv("CODEBASEOS_OBJECT_STORAGE_SECRET_KEY"),
            "auth_provider": os.getenv("CODEBASEOS_AUTH_PROVIDER", "github"),
            "session_secret": os.getenv("CODEBASEOS_SESSION_SECRET"),
            "supabase_jwt_secret": os.getenv("CODEBASEOS_SUPABASE_JWT_SECRET"),
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
