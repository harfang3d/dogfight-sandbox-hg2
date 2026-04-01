#!/usr/bin/env python3
"""Export static aircraft carrier deck metadata for RL landing research."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve()
SOURCE_ROOT = SCRIPT_PATH.parents[1]
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from carrier_deck_data import DEFAULT_JSON_OUTPUT_PATH, build_local_carrier_deck_data, render_json


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_JSON_OUTPUT_PATH,
        help="Output JSON path. Defaults to source/scripts/aircraft_carrier_deck_parameters.json",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit non-zero if the generated JSON differs from the target file.",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Print the generated JSON to stdout instead of writing the file.",
    )
    args = parser.parse_args()

    payload = render_json(build_local_carrier_deck_data())

    if args.stdout:
        sys.stdout.write(payload)
        return 0

    output_path = args.output.resolve()
    if args.check:
        if not output_path.exists():
            print(f"Missing output file: {output_path}", file=sys.stderr)
            return 1
        current = output_path.read_text(encoding="utf-8")
        if current != payload:
            print(f"Out-of-date output file: {output_path}", file=sys.stderr)
            return 1
        print(f"Carrier deck metadata is up to date: {output_path}")
        return 0

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(payload, encoding="utf-8")
    print(f"Wrote carrier deck metadata: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
