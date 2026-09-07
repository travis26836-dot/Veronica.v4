import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "runtime_isolation", Path(__file__).resolve().parents[1] / "scripts/prepare_runpod_model.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_matched_runtime_does_not_inherit_image_packages():
    arguments = module.runtime_environment_arguments({"isolatedEnvironment": True}, "/runtime")
    assert arguments == ["uv", "venv", "--python", "python3", "/runtime"]


def test_legacy_runtime_retains_existing_behavior():
    assert "--system-site-packages" in module.runtime_environment_arguments({}, "/runtime")


def test_invalid_isolation_flag_is_rejected():
    with pytest.raises(ValueError):
        module.runtime_environment_arguments({"isolatedEnvironment": "false"}, "/runtime")
