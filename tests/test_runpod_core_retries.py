"""A single transient connection reset must not throw away an entire paid Pod."""
import importlib.util
from http.client import RemoteDisconnected
from pathlib import Path
from unittest.mock import patch

import pytest
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("runpod_core_retries", ROOT / "scripts/runpod_core.py")
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)


def test_fetch_with_retries_recovers_from_one_transient_error():
    calls = {"count": 0}

    def flaky(url, payload=None, key=None):
        calls["count"] += 1
        if calls["count"] == 1:
            raise RemoteDisconnected("reset by peer")
        return b'{"ok": true}'

    with patch.object(core, "fetch", side_effect=flaky), patch.object(core.time, "sleep") as sleep:
        result = core.fetch_with_retries("http://127.0.0.1:18000/v1/models")
    assert result == b'{"ok": true}'
    assert calls["count"] == 2
    sleep.assert_called_once()


def test_fetch_with_retries_gives_up_after_exhausting_attempts():
    with patch.object(core, "fetch", side_effect=RemoteDisconnected("reset by peer")) as fetch, \
         patch.object(core.time, "sleep"):
        with pytest.raises(RemoteDisconnected):
            core.fetch_with_retries("http://127.0.0.1:18000/v1/models", attempts=3)
    assert fetch.call_count == 3


def test_fetch_with_retries_does_not_retry_a_real_http_error():
    # An auth rejection or other real HTTP status is not a network blip; it
    # must surface immediately so the caller's own handling (e.g. the
    # unauthenticated-access check) still works correctly.
    error = HTTPError("http://127.0.0.1:18000/v1/models", 401, "unauthorized", {}, None)
    with patch.object(core, "fetch", side_effect=error) as fetch:
        with pytest.raises(HTTPError):
            core.fetch_with_retries("http://127.0.0.1:18000/v1/models")
    assert fetch.call_count == 1
