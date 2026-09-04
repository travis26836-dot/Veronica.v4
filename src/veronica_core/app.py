from __future__ import annotations

import json
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, StrictBool

from .config import Settings
from .persona import MODE_PROMPTS, prepare_messages
from .provider import ChatProvider, OpenAICompatibleProvider, ProviderError, StreamingNotSupported


STATIC_DIR = Path(__file__).parent / "static"
LOOPBACK_HOSTS = {"127.0.0.1", "::1", "localhost", "testclient"}


class ChatMessage(BaseModel):
    model_config = ConfigDict(extra="allow")
    role: Literal["system", "developer", "user", "assistant", "tool"]
    content: str | list[dict[str, Any]] | None = None


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="allow")
    model: str | None = None
    messages: list[ChatMessage] = Field(min_length=1)
    veronica_mode: Literal["chat", "deep-reasoning", "creative", "coding"] = "chat"
    stream: StrictBool = False


def rewrite_sse_line(line: str, public_model: str) -> str:
    line = line.rstrip("\r")
    if not line.startswith("data:"):
        return line
    data = line[5:].strip()
    if data in {"", "[DONE]"}:
        return line
    try:
        payload = json.loads(data)
    except ValueError:
        return line
    if isinstance(payload, dict) and "model" in payload:
        payload["model"] = public_model
        return "data: " + json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    return line


def create_app(
    settings: Settings | None = None,
    provider: ChatProvider | None = None,
) -> FastAPI:
    settings = settings or Settings.from_environment()
    provider = provider or OpenAICompatibleProvider(settings)

    app = FastAPI(
        title="Veronica Core",
        version="0.1.0",
        description="Capability-preserving agent wrapper for Veronica.v4",
    )
    app.mount("/assets", StaticFiles(directory=STATIC_DIR), name="assets")

    @app.get("/", include_in_schema=False)
    async def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/api/health")
    async def health() -> dict[str, Any]:
        provider_health = await provider.health()
        return {
            "status": "ready" if provider_health.get("model_available") else "wrapper_only",
            "wrapper": "ready",
            "provider": provider_health,
            "public_model": settings.public_model,
            "upstream_configured": bool(settings.upstream_model),
        }

    @app.get("/api/capabilities")
    async def capabilities(request: Request) -> dict[str, Any]:
        host = request.client.host if request.client else ""
        return {
            "implemented": [
                "basic_text_chat",
                "streaming_chat",
                "persona_wrapper",
                "mode_selection",
                "openai_compatible_alias",
                "provider_health",
            ],
            "modes": list(MODE_PROMPTS),
            "mode_control": "prompt_presets_only; native reasoning controls require model qualification",
            "foundation_qualification": "pending",
            "local_access": "intended for loopback; no authentication yet",
            "loopback_client": host in LOOPBACK_HOSTS or host.startswith("127."),
            "browser_session": [
                "localStorage_persistence",
                "message_retry",
                "stop_generation",
                "copy",
                "regenerate",
                "safe_markdown",
            ],
            "planned": [
                "native_tool_execution",
                "scoped_memory",
                "personality_adapter",
                "application_modules",
                "serverless_deployment",
            ],
        }

    @app.get("/v1/models")
    async def models() -> dict[str, Any]:
        return {
            "object": "list",
            "data": [
                {
                    "id": settings.public_model,
                    "object": "model",
                    "owned_by": "veronica-v4",
                }
            ],
        }

    def _upstream_payload(request: ChatRequest) -> dict[str, Any]:
        payload = request.model_dump(exclude={"veronica_mode"}, exclude_unset=True)
        payload["model"] = settings.upstream_model
        payload["messages"] = prepare_messages(payload["messages"], request.veronica_mode)
        payload["stream"] = request.stream
        return payload

    async def _relay_sse(chunks: AsyncIterator[bytes]) -> AsyncIterator[bytes]:
        buffer = b""
        async for chunk in chunks:
            buffer += chunk
            while True:
                newline = buffer.find(b"\n")
                if newline < 0:
                    break
                line = buffer[:newline].decode("utf-8", errors="replace")
                buffer = buffer[newline + 1 :]
                yield (rewrite_sse_line(line, settings.public_model) + "\n").encode("utf-8")
        if buffer:
            line = buffer.decode("utf-8", errors="replace")
            yield (rewrite_sse_line(line, settings.public_model) + "\n").encode("utf-8")

    @app.post("/v1/chat/completions")
    async def chat_completions(request: ChatRequest) -> Any:
        upstream_payload = _upstream_payload(request)
        if not request.stream:
            try:
                response = await provider.complete(upstream_payload)
            except ProviderError as exc:
                raise HTTPException(status_code=503, detail=str(exc)) from exc
            response["model"] = settings.public_model
            return response

        stream_fn = getattr(provider, "stream", None)
        if stream_fn is None:
            raise HTTPException(
                status_code=501,
                detail="The configured model provider does not support streaming; use stream=false.",
            )

        agen = stream_fn(upstream_payload)
        try:
            first = await anext(agen)
            while not first:
                first = await anext(agen)
        except StopAsyncIteration:
            raise HTTPException(status_code=502, detail="The model provider returned an empty stream.") from None
        except StreamingNotSupported as exc:
            raise HTTPException(status_code=501, detail=str(exc)) from exc
        except ProviderError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

        async def generate() -> AsyncIterator[bytes]:
            async def combined() -> AsyncIterator[bytes]:
                yield first
                async for chunk in agen:
                    yield chunk

            try:
                async for chunk in _relay_sse(combined()):
                    yield chunk
            except StreamingNotSupported as exc:
                payload = {"error": {"message": str(exc), "code": "streaming_unsupported"}}
                yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n".encode()
            except ProviderError as exc:
                payload = {"error": {"message": str(exc), "code": "provider_unavailable"}}
                yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n".encode()

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache, no-transform",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    return app
