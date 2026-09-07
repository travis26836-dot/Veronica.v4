from __future__ import annotations

from pathlib import Path
import subprocess
from typing import Any

from fastapi.testclient import TestClient

from veronica_core.app import create_app, rewrite_sse_line
from veronica_core.config import Settings
from veronica_core.provider import ProviderError, StreamingNotSupported


SETTINGS = Settings(
    public_model="Veronica",
    upstream_base_url="http://provider.test/v1",
    upstream_model="candidate/model",
    upstream_api_key=None,
    provider_timeout_seconds=5,
)

ROOT = Path(__file__).resolve().parents[1]


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

    async def stream(self, payload: dict[str, Any]):
        self.last_payload = payload
        yield b'data: {"id":"chatcmpl-test","object":"chat.completion.chunk","model":"candidate/model","choices":[{"index":0,"delta":{"role":"assistant","content":"Core"}}]}\n\n'
        yield b'data: {"id":"chatcmpl-test","object":"chat.completion.chunk","model":"candidate/model","choices":[{"index":0,"delta":{"content":" res'
        yield b'ponse"},"finish_reason":null}]}\n\n'
        yield b"data: [DONE]\n\n"


class OfflineProvider(MockProvider):
    async def health(self) -> dict[str, Any]:
        return {"reachable": False, "model_available": False, "error": "ConnectError"}

    async def complete(self, payload: dict[str, Any]) -> dict[str, Any]:
        raise ProviderError("Provider offline")

    async def stream(self, payload: dict[str, Any]):
        self.last_payload = payload
        raise ProviderError("Provider offline")
        yield b""


class CompleteOnlyProvider:
    async def health(self) -> dict[str, Any]:
        return {"reachable": True, "model_available": True, "status_code": 200}

    async def complete(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": "chatcmpl-test",
            "object": "chat.completion",
            "model": "candidate/model",
            "choices": [{"index": 0, "message": {"role": "assistant", "content": "Core response"}, "finish_reason": "stop"}],
        }


class NoStreamProvider(MockProvider):
    async def stream(self, payload: dict[str, Any]):
        self.last_payload = payload
        raise StreamingNotSupported("The configured model provider does not support streaming.")
        yield b""


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
    assert provider.last_payload["stream"] is False
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


def test_provider_failure_is_honest() -> None:
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
    assert streaming.status_code == 503


def test_streaming_forwards_sse_and_rewrites_model() -> None:
    provider = MockProvider()
    client = TestClient(create_app(SETTINGS, provider))
    response = client.post(
        "/v1/chat/completions",
        json={"messages": [{"role": "user", "content": "Hello"}], "stream": True, "veronica_mode": "coding"},
    )
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    assert "candidate/model" not in response.text
    assert '"model":"Veronica"' in response.text
    assert "Core" in response.text
    assert "response" in response.text
    assert "data: [DONE]" in response.text
    assert provider.last_payload is not None
    assert provider.last_payload["stream"] is True
    assert provider.last_payload["model"] == "candidate/model"
    assert "veronica_mode" not in provider.last_payload
    assert "rigorous software collaborator" in provider.last_payload["messages"][1]["content"]


def test_streaming_unsupported_is_not_faked() -> None:
    missing = TestClient(create_app(SETTINGS, CompleteOnlyProvider())).post(
        "/v1/chat/completions",
        json={"messages": [{"role": "user", "content": "Hello"}], "stream": True},
    )
    assert missing.status_code == 501
    assert "does not support streaming" in missing.json()["detail"]

    refused = TestClient(create_app(SETTINGS, NoStreamProvider())).post(
        "/v1/chat/completions",
        json={"messages": [{"role": "user", "content": "Hello"}], "stream": True},
    )
    assert refused.status_code == 501
    assert "does not support streaming" in refused.json()["detail"]


def test_rewrite_sse_line_maps_public_alias() -> None:
    rewritten = rewrite_sse_line(
        'data: {"model":"candidate/model","choices":[{"delta":{"content":"Hi"}}]}',
        "Veronica",
    )
    assert '"model":"Veronica"' in rewritten
    assert "candidate/model" not in rewritten
    assert rewrite_sse_line("data: [DONE]", "Veronica") == "data: [DONE]"
    assert rewrite_sse_line("event: delta", "Veronica") == "event: delta"


def test_capability_report_separates_implemented_and_planned() -> None:
    response = TestClient(create_app(SETTINGS, MockProvider())).get("/api/capabilities")
    body = response.json()
    assert "basic_text_chat" in body["implemented"]
    assert "streaming_chat" in body["implemented"]
    assert "streaming" not in body["planned"]
    assert "native_tool_execution" in body["planned"]
    assert "native_tool_execution" not in body["implemented"]
    assert body["local_access"].startswith("intended for loopback")
    assert "localStorage_persistence" in body["browser_session"]


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
    page = client.get("/")
    js = client.get("/assets/app.js")
    css = client.get("/assets/styles.css")
    assert page.status_code == 200
    assert "No model-generated response" in page.text
    assert "stopChat" in page.text
    assert "blackhole-background.js" not in page.text
    assert js.status_code == 200
    assert "drawStarfield" in js.text
    assert "startVeronicaHorizon" not in js.text
    assert "localStorage" in js.text
    assert "AbortController" in js.text
    assert "markdownToSafeHtml" in js.text
    assert "data-action" in js.text
    assert "streaming_chat" in js.text
    assert css.status_code == 200
    assert "message-actions" in css.text
    assert "cosmic-background.png" in css.text
    assert client.get("/assets/assets/cosmic-background.png").status_code == 200
    assert client.get("/assets/assets/veronica-logo-mark.png").status_code == 200


def test_chat_javascript_parses_and_markdown_is_safe() -> None:
    parsed = subprocess.run(
        ["node", "--check", str(ROOT / "src/veronica_core/static/app.js")],
        capture_output=True,
        text=True,
        check=False,
    )
    assert parsed.returncode == 0, parsed.stderr
    markdown = subprocess.run(
        ["node", str(Path(__file__).with_name("test_chat_markdown.js"))],
        capture_output=True,
        text=True,
        check=False,
    )
    assert markdown.returncode == 0, markdown.stdout + markdown.stderr
