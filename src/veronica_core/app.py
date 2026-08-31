from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, StrictBool
from typing import Literal

from .config import Settings
from .persona import MODE_PROMPTS, prepare_messages
from .provider import ChatProvider, OpenAICompatibleProvider, ProviderError


STATIC_DIR = Path(__file__).parent / "static"


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
    async def capabilities() -> dict[str, Any]:
        return {
            "implemented": [
                "basic_text_chat",
                "persona_wrapper",
                "mode_selection",
                "openai_compatible_alias",
                "provider_health",
            ],
            "modes": list(MODE_PROMPTS),
            "mode_control": "prompt_presets_only; native reasoning controls require model qualification",
            "foundation_qualification": "pending",
            "planned": [
                "streaming",
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

    @app.post("/v1/chat/completions")
    async def chat_completions(request: ChatRequest) -> dict[str, Any]:
        if request.stream:
            raise HTTPException(
                status_code=501,
                detail="Streaming is a planned milestone; use stream=false for basic chat.",
            )

        upstream_payload = request.model_dump(exclude={"veronica_mode"}, exclude_unset=True)
        prepared = prepare_messages(upstream_payload["messages"], request.veronica_mode)
        upstream_payload["model"] = settings.upstream_model
        upstream_payload["messages"] = prepared
        upstream_payload["stream"] = False

        try:
            response = await provider.complete(upstream_payload)
        except ProviderError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

        response["model"] = settings.public_model
        return response

    return app
