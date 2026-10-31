import pytest

from second_brain.config import settings
from second_brain.sources import embedder


@pytest.fixture(autouse=True)
def _reset_client(monkeypatch):
    monkeypatch.setattr(embedder, "_client", None)
    monkeypatch.setattr(settings, "embedding_model", "text-embedding-3-small")


def test_uses_openai_when_openai_key_set(monkeypatch):
    monkeypatch.setattr(settings, "openai_api_key", "sk-openai")
    monkeypatch.setattr(settings, "openrouter_api_key", "sk-or")
    client = embedder._get_client()
    assert client.api_key == "sk-openai"
    assert "openrouter" not in str(client.base_url)
    assert embedder._provider_model() == "text-embedding-3-small"


def test_falls_back_to_openrouter_without_openai_key(monkeypatch):
    monkeypatch.setattr(settings, "openai_api_key", "")
    monkeypatch.setattr(settings, "openrouter_api_key", "sk-or")
    client = embedder._get_client()
    assert client.api_key == "sk-or"
    assert str(client.base_url).startswith(settings.openrouter_base_url)
    assert embedder._provider_model() == "openai/text-embedding-3-small"


def test_keeps_already_namespaced_model_on_openrouter(monkeypatch):
    monkeypatch.setattr(settings, "openai_api_key", "")
    monkeypatch.setattr(settings, "openrouter_api_key", "sk-or")
    monkeypatch.setattr(settings, "embedding_model", "openai/text-embedding-3-large")
    assert embedder._provider_model() == "openai/text-embedding-3-large"
