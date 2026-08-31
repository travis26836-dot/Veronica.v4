from __future__ import annotations

from typing import Any, Protocol

import httpx

from .config import Settings


class ProviderError(RuntimeError):
    pass


class ChatProvider(Protocol):
    async def health(self) -> dict[str, Any]: ...

    async def complete(self, payload: dict[str, Any]) -> dict[str, Any]: ...


class OpenAICompatibleProvider:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.settings.upstream_api_key:
            headers["Authorization"] = f"Bearer {self.settings.upstream_api_key}"
        return headers

    async def health(self) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{self.settings.upstream_base_url}/models",
                    headers=self._headers(),
                )
                response.raise_for_status()
                data = response.json()
            if not isinstance(data, dict) or not isinstance(data.get("data"), list):
                raise ValueError("Invalid models response")
            available = any(
                isinstance(item, dict) and item.get("id") == self.settings.upstream_model
                for item in data["data"]
            )
            return {
                "reachable": True,
                "model_available": available,
                "status_code": response.status_code,
            }
        except (httpx.HTTPError, ValueError) as exc:
            return {"reachable": False, "model_available": False, "error": type(exc).__name__}

    async def complete(self, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(
                timeout=self.settings.provider_timeout_seconds
            ) as client:
                response = await client.post(
                    f"{self.settings.upstream_base_url}/chat/completions",
                    headers=self._headers(),
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise ProviderError(
                "The configured model provider is unavailable or returned an invalid response."
            ) from exc

        if (
            not isinstance(data, dict)
            or not isinstance(data.get("choices"), list)
            or not data["choices"]
            or not isinstance(data["choices"][0], dict)
            or not isinstance(data["choices"][0].get("message"), dict)
        ):
            raise ProviderError("The configured model provider returned an invalid chat completion.")
        return data
