from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from veronica_core.app import create_app
from veronica_core.config import Settings
from veronica_core.provider import ProviderError


SETTINGS = Settings(
    public_model="Veronica",
    upstream_base_url="http://provider.test/v1",
    upstream_model="candidate/model",
    upstream_api_key=None,
    provider_timeout_seconds=5,
)


class MockProvider:
    def __init__(self) -> None:
        self.last_payload: dict[str, Any] | None = None

    async def health(self) -> dict[str, Any]:
        return {"reachable": True, "model_available": True, "status_code": 200}

    async def complete(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.last_payload = payload
        return {
            "id": "chatcmpl-test",
            "object": "chat.completion",
            "model": "candidate/model",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": "Core response"},
                    "finish_reason": "stop",
                }
            ],
        }


class OfflineProvider(MockProvider):
    async def health(self) -> dict[str, Any]:
        return {"reachable": False, "model_available": False, "error": "ConnectError"}

    async def complete(self, payload: dict[str, Any]) -> dict[str, Any]:
        raise ProviderError("Provider offline")


def test_health_distinguishes_wrapper_and_provider() -> None:
    online = TestClient(create_app(SETTINGS, MockProvider())).get("/api/health")
    assert online.status_code == 200
    assert online.json()["status"] == "ready"

    offline = TestClient(create_app(SETTINGS, OfflineProvider())).get("/api/health")
    assert offline.status_code == 200
    assert offline.json()["status"] == "wrapper_only"


def test_models_exposes_only_stable_veronica_alias() -> None:
    response = TestClient(create_app(SETTINGS, MockProvider())).get("/v1/models")
    assert response.status_code == 200
    assert response.json()["data"][0]["id"] == "Veronica"
    assert "candidate/model" not in response.text


def test_chat_injects_persona_mode_and_maps_model() -> None:
    provider = MockProvider()
    client = TestClient(create_app(SETTINGS, provider))
    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "Veronica",
            "messages": [{"role": "user", "content": "Be sarcastic."}],
            "veronica_mode": "creative",
        },
    )

    assert response.status_code == 200
    assert response.json()["model"] == "Veronica"
    assert provider.last_payload is not None
    assert provider.last_payload["model"] == "candidate/model"
    assert provider.last_payload["messages"][0]["role"] == "system"
    assert "highly capable" in provider.last_payload["messages"][0]["content"]
    assert "vivid, original language" in provider.last_payload["messages"][1]["content"]
    assert provider.last_payload["messages"][-1]["content"] == "Be sarcastic."
    assert "veronica_mode" not in provider.last_payload


def test_invalid_requests_stop_before_provider() -> None:
    provider = MockProvider()
    client = TestClient(create_app(SETTINGS, provider))

    missing = client.post("/v1/chat/completions", json={"model": "Veronica"})
    assert missing.status_code == 422
    assert provider.last_payload is None

    bad_mode = client.post(
        "/v1/chat/completions",
        json={"messages": [{"role": "user", "content": "Hello"}], "veronica_mode": "magic"},
    )
    assert bad_mode.status_code == 422
    assert provider.last_payload is None


def test_provider_failure_is_honest_and_streaming_is_not_faked() -> None:
    client = TestClient(create_app(SETTINGS, OfflineProvider()))
    failed = client.post(
        "/v1/chat/completions",
        json={"messages": [{"role": "user", "content": "Hello"}]},
    )
    assert failed.status_code == 503

    streaming = client.post(
        "/v1/chat/completions",
        json={"messages": [{"role": "user", "content": "Hello"}], "stream": True},
    )
    assert streaming.status_code == 501


def test_capability_report_separates_implemented_and_planned() -> None:
    response = TestClient(create_app(SETTINGS, MockProvider())).get("/api/capabilities")
    body = response.json()
    assert "basic_text_chat" in body["implemented"]
    assert "native_tool_execution" in body["planned"]
    assert "native_tool_execution" not in body["implemented"]


def test_system_messages_and_native_tool_fields_are_preserved() -> None:
    provider = MockProvider()
    client = TestClient(create_app(SETTINGS, provider))
    tool = {"type": "function", "function": {"name": "get_time", "parameters": {"type": "object"}}}
    source_messages = [
        {"role": "system", "content": "Use metric units."},
        {"role": "user", "content": "What time is it?"},
    ]
    response = client.post(
        "/v1/chat/completions",
        json={"messages": source_messages, "tools": [tool], "tool_choice": "auto"},
    )
    assert response.status_code == 200
    assert provider.last_payload is not None
    assert provider.last_payload["messages"][2:] == source_messages
    assert provider.last_payload["tools"] == [tool]
    assert provider.last_payload["tool_choice"] == "auto"


def test_malformed_message_and_mode_types_are_rejected() -> None:
    provider = MockProvider()
    client = TestClient(create_app(SETTINGS, provider))
    for payload in [
        {"messages": ["not a message"]},
        {"messages": [{"role": "invalid", "content": "Hello"}]},
        {"messages": [{"role": "user", "content": "Hello"}], "veronica_mode": []},
        {"messages": [{"role": "user", "content": "Hello"}], "stream": "true"},
    ]:
        assert client.post("/v1/chat/completions", json=payload).status_code == 422
    assert provider.last_payload is None


def test_static_chat_interface_is_served() -> None:
    client = TestClient(create_app(SETTINGS, MockProvider()))
    assert client.get("/").status_code == 200
    assert "No model-generated response" in client.get("/").text
    assert client.get("/assets/app.js").status_code == 200
    assert client.get("/assets/styles.css").status_code == 200
    assert client.get("/assets/assets/cosmic-background.png").status_code == 200
    assert client.get("/assets/assets/veronica-logo-mark.png").status_code == 200
