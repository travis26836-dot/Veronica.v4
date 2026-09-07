import json
from pathlib import Path

import pytest

from scripts.remote_start import read_profile, validate_request, write_approval


def test_remote_start_requires_explicit_authorization():
    with pytest.raises(ValueError, match="START_VERONICA"):
        validate_request(60, "yes", read_profile())


def test_remote_start_accepts_profile_duration():
    validate_request(60, "START_VERONICA", read_profile())


def test_remote_start_rejects_duration_above_profile_limit():
    with pytest.raises(ValueError, match="duration"):
        validate_request(1441, "START_VERONICA", read_profile())


def test_approval_is_one_use_and_uses_pinned_profile(tmp_path: Path):
    run = tmp_path / "2026-09-07T000000Z-start-veronica"
    approval = write_approval(run, 60, "START_VERONICA")
    data = json.loads(approval.read_text())
    profile = read_profile()
    assert data["resourceCount"] == 1
    assert data["modelRevision"] == profile["model"]["revision"]
    with pytest.raises(ValueError, match="not empty"):
        write_approval(run, 60, "START_VERONICA")
