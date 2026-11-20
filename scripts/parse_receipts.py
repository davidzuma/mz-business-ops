#!/usr/bin/env python3
"""Extract basic receipt metadata from a text-readable PDF."""

import argparse
import re
import subprocess
from pathlib import Path


def extract_text(pdf_path: Path) -> str:
    result = subprocess.run(
        ["pdftotext", str(pdf_path), "-"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "pdftotext failed")
    return result.stdout


def parse_receipt(pdf_path: Path) -> dict[str, object]:
    text = extract_text(pdf_path)
    totals = [
        float(match.replace(",", "").replace("€", "").strip())
        for match in re.findall(r"(?:€\s*)\d+(?:,\d{3})*(?:\.\d{2})?", text)
    ]
    return {
        "file": str(pdf_path),
        "text": text,
        "total": max(totals) if totals else None,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    args = parser.parse_args()
    print(parse_receipt(args.input))


if __name__ == "__main__":
    main()
