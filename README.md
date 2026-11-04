
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

    if not root.exists():
        print(f"Error: Directory {root} does not exist")
        sys.exit(1)

    for path in root.rglob("*"):
        # Skip directories and symlinks
        if not path.is_file() or path.is_symlink():
            continue
        # Skip the baseline file itself if inside the scanned folder
        if path.name == BASELINE_FILE.name:
            continue
        try:
            relative = str(path.relative_to(root))
            results[relative] = calculate_hash(path)
        except Exception as e:
            print(f"Skipping {path}: {e}")
            continue
    return results

def save_baseline(data, output_path):
    output_path = Path(output_path)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
    print(f"[+] Baseline saved to {output_path} ({len(data)} files)")

def load_baseline(baseline_path):
    baseline_path = Path(baseline_path)
    if not baseline_path.exists():
        print(f"Error: Baseline file {baseline_path} not found. Run with --create first.")
        sys.exit(1)
    with baseline_path.open("r", encoding="utf-8") as f:
        return json.load(f)

def compare_baselines(current, baseline):
    added = set(current) - set(baseline)
    removed = set(baseline) - set(current)
    modified = {f for f in set(current) & set(baseline) if current[f] != baseline[f]}

    if not added and not removed and not modified:
        print("[OK] No changes detected. Integrity verified.")
        return

    if added:
        print("\n[+] Added files:")
        for f in sorted(added):
            print(f"  + {f}")
    if removed:
        print("\n[-] Removed files:")
        for f in sorted(removed):
            print(f"  - {f}")
    if modified:
        print("\n[!] Modified files:")
        for f in sorted(modified):
            print(f"  * {f}")
            print(f"      old: {baseline[f][:16]}... new: {current[f][:16]}...")

def main():
    parser = argparse.ArgumentParser(
        description="File Integrity Monitor - SHA-256 baseline checker",
        epilog="Example: python integrity.py --create /path/to/folder  or  python integrity.py --check /path/to/folder"
    )
    parser.add_argument("directory", help="Directory to scan")
    parser.add_argument("--create", action="store_true", help="Create new baseline file")
    parser.add_argument("--check", action="store_true", help="Check against existing baseline")
    parser.add_argument("--baseline", default=str(BASELINE_FILE), help=f"Baseline file path (default: {BASELINE_FILE})")

    args = parser.parse_args()

    if args.create and args.check:
        parser.error("Use --create OR --check, not both")

    # Default action: if no flag, create if baseline doesn't exist else check
    if not args.create and not args.check:
        if Path(args.baseline).exists():
            args.check = True
        else:
            args.create = True

    current_scan = scan_directory(args.directory)

    if args.create:
        save_baseline(current_scan, args.baseline)
    elif args.check:
        baseline_data = load_baseline(args.baseline)
        compare_baselines(current_scan, baseline_data)

if __name__ == "__main__":
    main()