import pytest

from codebase_os.config import Settings
from codebase_os.model_factory import build_model_provider
from codebase_os.model_providers import AnthropicProvider, GeminiProvider, OpenAICompatibleProvider


def settings(provider, **kwargs):
    return Settings(model_provider=provider, model_api_key="key", model_name="model", **kwargs)


def test_factory_selects_openai_compatible_aliases():
    for name in ("openai", "groq", "cerebras", "together", "openrouter", "openai-compatible"):
        assert isinstance(build_model_provider(settings(name, model_base_url="https://example.test/v1")), OpenAICompatibleProvider)


def test_factory_selects_anthropic_and_gemini():
    assert isinstance(build_model_provider(settings("anthropic", model_base_url="https://example.test")), AnthropicProvider)
    assert isinstance(build_model_provider(settings("gemini", model_base_url="https://example.test")), GeminiProvider)


def test_factory_none_mode_returns_none():
    assert build_model_provider(Settings(model_provider="none")) is None


def test_factory_rejects_missing_provider_configuration():
    with pytest.raises(ValueError, match="model API key"):
        build_model_provider(Settings(model_provider="groq", model_name="model", model_base_url="https://example.test"))


def test_factory_rejects_placeholder_credentials():
    with pytest.raises(ValueError, match="model API key"):
        build_model_provider(Settings(
            model_provider="groq",
            model_api_key="replace-with-groq-api-key",
            model_name="replace-with-groq-model",
            model_base_url="https://api.groq.com/openai/v1",
        ))
