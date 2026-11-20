#!/usr/bin/env python3
"""Validate CRM synchronization input without changing external systems."""

import argparse
import csv
from pathlib import Path


def validate_csv(input_path: Path) -> list[dict[str, str]]:
    with input_path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    rows = validate_csv(args.input)
    print(f"Validated {len(rows)} CRM rows from {args.input}")
    if not args.dry_run:
        raise SystemExit("Refusing CRM synchronization without --dry-run")


if __name__ == "__main__":
    main()
