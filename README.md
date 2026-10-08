#!/usr/bin/env python3

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

BASELINE_FILE = Path("integrity_baseline.json")


def calculate_hash(file_path):
    """Calculate the SHA-256 hash of a file."""
    digest = hashlib.sha256()

    with file_path.open("rb") as file:
        for chunk in iter(lambda: file.read(65536), b""):
            digest.update(chunk)

    return digest.hexdigest()


def scan_directory(directory):
    """Hash regular files without following directory symlinks."""
    results = {}
    root = Path(directory).resolve()

    if not root.is_dir():
        raise ValueError(f"Not a directory: {root}")

    for current_root, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = [
            name for name in dirs
            if not (Path(current_root) / name).is_symlink()
        ]

        for name in files:
            file_path = Path(current_root) / name

            if file_path.is_symlink() or not file_path.is_file():
                continue

            try:
                relative_path = str(file_path.relative_to(root))
                results[relative_path] = calculate_hash(file_path)
            except (OSError, PermissionError) as error:
                print(f"[WARNING] Cannot read {file_path}: {error}")

    return results


def load_baseline():
    with BASELINE_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_baseline(results):
    temporary_file = BASELINE_FILE.with_suffix(".tmp")

    with temporary_file.open("w", encoding="utf-8") as file:
        json.dump(results, file, indent=2, sort_keys=True)

    temporary_file.replace(BASELINE_FILE)


def compare_results(old, new):
    old_files = set(old)
    new_files = set(new)

    for name in sorted(new_files - old_files):
        print(f"[NEW FILE] {name}")

    for name in sorted(old_files - new_files):
        print(f"[MISSING FILE] {name}")

    for name in sorted(old_files & new_files):
        if old[name] != new[name]:
            print(f"[MODIFIED FILE] {name}")

    if old == new:
        print("[OK] No file changes detected.")


def main():
    parser = argparse.ArgumentParser(
        description="Monitor file integrity using SHA-256."
    )

    parser.add_argument(
        "directory",
        help="Directory to monitor"
    )

    parser.add_argument(
        "--init",
        action="store_true",
        help="Create or replace the baseline"
    )

    args = parser.parse_args()

    try:
        current = scan_directory(args.directory)

        if args.init:
            save_baseline(current)
            print(f"[OK] Baseline saved for {len(current)} files.")
            return

        if not BASELINE_FILE.exists():
            print(
                "[ERROR] No baseline found. "
                "Run with --init first.",
                file=sys.stderr
            )
            sys.exit(1)

        baseline = load_baseline()
        compare_results(baseline, current)

    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"[ERROR] {error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

# Disclaimer
**Notice**

    This project is run on my own virtual box machines and set up. The code in this project can be and should be editied to fit your ip and mac address specifications. Ideal set up is necessary for proper efficeny.
---
***WARNING***

THIS PROJECT IS NOT USED FOR MALLICIOUS INTENT AND IS AN EDUCATIONAL PROJECT USED TO SHOWCASE MY ABILITIES AS A ETHICAL HACKER.
IF THIS CODE IS UTILIZED IN ANY FORM OF MALLICIOUS INTENT, BE INFORMED THAT PROPER LEAGAL COURSE OF ACTION CAN BE TAKEN ON THOSE WHO USE IT ,BY LAW ENFORCEMENT AGENCIES.
