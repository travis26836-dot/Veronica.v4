import asyncio

import httpx
import pytest

from veronica_core.config import Settings
from veronica_core.provider import OpenAICompatibleProvider, ProviderError


SETTINGS = Settings(
    public_model="Veronica",
    upstream_base_url="http://provider.test/v1",
    upstream_model="candidate/model",
    upstream_api_key="test-secret",
    provider_timeout_seconds=5,
)


def transport_for(monkeypatch, handler):
    original_client = httpx.AsyncClient
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kwargs: original_client(transport=httpx.MockTransport(handler), **kwargs),
    )


def test_health_requires_the_configured_model(monkeypatch) -> None:
    transport_for(monkeypatch, lambda request: httpx.Response(200, json={"data": [{"id": "other/model"}]}))
    health = asyncio.run(OpenAICompatibleProvider(SETTINGS).health())
    assert health["reachable"] is True
    assert health["model_available"] is False


def test_provider_forwards_auth_but_never_returns_it(monkeypatch) -> None:
    def handler(request):
        assert request.headers["authorization"] == "Bearer test-secret"
        assert request.url.path == "/v1/chat/completions"
        return httpx.Response(200, json={"choices": [{"message": {"role": "assistant", "content": "Hello"}}]})

    transport_for(monkeypatch, handler)
    result = asyncio.run(OpenAICompatibleProvider(SETTINGS).complete({"messages": []}))
    assert "test-secret" not in str(result)


def test_invalid_chat_response_is_rejected(monkeypatch) -> None:
    transport_for(monkeypatch, lambda request: httpx.Response(200, json={"unexpected": True}))
    with pytest.raises(ProviderError, match="invalid chat completion"):
        asyncio.run(OpenAICompatibleProvider(SETTINGS).complete({"messages": []}))


def test_provider_error_does_not_expose_response_or_credentials(monkeypatch) -> None:
    transport_for(monkeypatch, lambda request: httpx.Response(401, text="test-secret private provider details"))
    with pytest.raises(ProviderError) as error:
        asyncio.run(OpenAICompatibleProvider(SETTINGS).complete({"messages": []}))
    assert "test-secret" not in str(error.value)
    assert "private provider" not in str(error.value)
