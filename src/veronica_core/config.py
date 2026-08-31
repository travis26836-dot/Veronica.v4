from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True, slots=True)
class Settings:
    public_model: str
    upstream_base_url: str
    upstream_model: str
    upstream_api_key: str | None
    provider_timeout_seconds: float

    @classmethod
    def from_environment(cls) -> "Settings":
        api_key = os.getenv("VERONICA_UPSTREAM_API_KEY", "").strip() or None
        return cls(
            public_model=os.getenv("VERONICA_PUBLIC_MODEL", "Veronica").strip() or "Veronica",
            upstream_base_url=os.getenv(
                "VERONICA_UPSTREAM_BASE_URL", "http://127.0.0.1:8000/v1"
            ).rstrip("/"),
            upstream_model=os.getenv(
                "VERONICA_UPSTREAM_MODEL",
                "huihui-ai/Huihui-Qwen3-30B-A3B-Instruct-2507-abliterated",
            ).strip(),
            upstream_api_key=api_key,
            provider_timeout_seconds=float(
                os.getenv("VERONICA_PROVIDER_TIMEOUT_SECONDS", "180")
            ),
        )
