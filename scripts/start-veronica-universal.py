#!/usr/bin/env python3
"""Universal Veronica start command wrapper.

Usage examples:
  python scripts/start-veronica-universal.py --plan
  python scripts/start-veronica-universal.py --authorize-start --duration-minutes 60 \
    --requested-by codex --authorization-context "Owner requested Start Veronica for one hour."
"""
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from veronica_core.universal_start import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
