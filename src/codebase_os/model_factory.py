from pydantic import SecretStr

from .config import Settings
from .model_providers import AnthropicProvider, GeminiProvider, OpenAICompatibleProvider, OpenAIProvider
from .model_transport import JsonTransport, UrllibTransport


COMPATIBLE = {"groq", "cerebras", "together", "openrouter", "openai-compatible"}


def _secret(value: SecretStr | None, label: str) -> str:
    if value is None or not value.get_secret_value().strip() or value.get_secret_value().lower().startswith("replace-with-"):
        raise ValueError(f"{label} is required")
    return value.get_secret_value()


def _model(settings: Settings) -> str:
    if not settings.model_name or not settings.model_name.strip() or settings.model_name.lower().startswith("replace-with-"):
        raise ValueError("model name is required")
    return settings.model_name


def build_model_provider(settings: Settings, transport: JsonTransport | None = None):
    provider = settings.model_provider
    if provider == "none":
        return None
    api_key = _secret(settings.model_api_key, "model API key")
    model = _model(settings)
    http = transport or UrllibTransport()
    if provider == "openai":
        return OpenAIProvider(settings.model_base_url or "https://api.openai.com/v1", api_key, model, http)
    if provider in COMPATIBLE:
        if not settings.model_base_url:
            raise ValueError("model base URL is required")
        return OpenAICompatibleProvider(settings.model_base_url, api_key, model, http)
    if provider == "anthropic":
        return AnthropicProvider(settings.model_base_url or "https://api.anthropic.com/v1", api_key, model, http)
    if provider == "gemini":
        return GeminiProvider(settings.model_base_url or "https://generativelanguage.googleapis.com/v1beta", api_key, model, http)
    raise ValueError(f"unsupported model provider: {provider}")
