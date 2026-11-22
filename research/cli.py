"""Command-line entry point for the checked-in demonstration workflows."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
from datetime import datetime, timezone
from pathlib import Path

from research.genomics import evaluate, leakage, validate_split

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures" / "demo.json"


def run(command: str):
    raw = FIXTURE.read_bytes()
    dataset = json.loads(raw)
    if command == "evaluate":
        result = evaluate(dataset["samples"])
    elif command == "leakage":
        result = leakage(dataset["samples"])
    else:
        result = validate_split(dataset["samples"])
    return {
        "manifest_version": 1,
        "command": command,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(),
        "fixture_id": dataset["id"],
        "fixture_sha256": hashlib.sha256(raw).hexdigest(),
        "result": result,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("evaluate", "leakage", "validate-split"))
    parser.add_argument("--output", type=Path, help="write the reproducibility manifest to this path")
    args = parser.parse_args()
    manifest = run(args.command)
    output = json.dumps(manifest, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output + "\n")
    print(output)


if __name__ == "__main__":
    main()
