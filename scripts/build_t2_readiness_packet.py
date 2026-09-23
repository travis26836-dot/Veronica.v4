"""Build or validate the offline CP4 T2 readiness packet."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from veronica_core import qualification_packet as packet


def _dependency(path_value: str | None, root: Path) -> dict | None:
    if not path_value:
        return None
    path = (root / path_value).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f"Evidence path escapes project root: {path_value}")
    return {"path": path_value}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("build", "validate"))
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--cp2-evidence", type=str)
    parser.add_argument("--cp3-evidence", type=str)
    args = parser.parse_args()
    root = packet.ROOT
    if args.command == "build":
        value = packet.build_packet(
            root=root,
            cp2=_dependency(args.cp2_evidence, root),
            cp3=_dependency(args.cp3_evidence, root),
        )
        packet.write_packet(args.packet, value)
        report = packet.validate_packet(value, root)
    else:
        value = json.loads(args.packet.read_text(encoding="utf-8-sig"))
        report = packet.validate_packet(value, root)
    if args.report:
        packet.write_report(args.report, report)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
