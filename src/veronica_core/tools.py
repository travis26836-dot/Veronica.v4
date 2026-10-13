"""Local tool execution. The image tool records a prompt and does not render."""
from __future__ import annotations

import json
from typing import Any


def execute_tool_call(call: dict[str, Any]) -> dict[str, Any]:
    function = call.get("function") if isinstance(call, dict) else None
    function = function if isinstance(function, dict) else {}
    name = function.get("name")
    result = {"tool_call_id": call.get("id") if isinstance(call, dict) else None, "name": name, "ok": False}
    raw = function.get("arguments")
    if isinstance(raw, str):
        try:
            arguments = json.loads(raw)
        except json.JSONDecodeError as error:
            result["error"] = f"invalid arguments: {error}"
            return result
    elif isinstance(raw, dict):
        arguments = raw
    else:
        result["error"] = "tool arguments must be a JSON object"
        return result
    if not isinstance(arguments, dict):
        result["error"] = "tool arguments must be a JSON object"
        return result
    if name != "render_image":
        result["error"] = f"unknown tool: {name}"
        return result
    prompt = arguments.get("prompt")
    if not isinstance(prompt, str) or not prompt.strip():
        result["error"] = "render_image requires a non-empty prompt"
        return result
    result["ok"] = True
    result["result"] = {"status": "not rendered", "prompt": prompt}
    return result
