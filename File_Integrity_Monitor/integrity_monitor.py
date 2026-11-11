# ============================================================
# File Integrity Monitor - by Batholomew Okoro
# Project: CyberSecurityProjects
# Purpose: Detect if any file has been changed, deleted, or added
# How it works: Uses SHA-256 hash to create a fingerprint for each file
# ============================================================

# Import needed tools
import argparse  # To read commands from terminal like --init, --scan
import hashlib   # To create SHA-256 hash (fingerprint) of files
import json      # To save/load baseline data as JSON file
import os        # To walk through folders and check files
import sys       # To exit program safely if error happens
from pathlib import Path  # To handle file paths easily

# Name of file where we save the original fingerprints
BASELINE_FILE = "baseline.json"

# ============================================================
# FUNCTION 1: Create SHA-256 hash of one file
# ============================================================
def get_file_hash(file_path):
    """Return SHA-256 hash of a file, or None if file cannot be read."""
    try:
        # Open file in binary read mode
        with open(file_path, "rb") as f:
            # Read file and create SHA-256 hash
            return hashlib.sha256(f.read()).hexdigest()
    except Exception as e:
        # If file cannot be read (permission, deleted), show warning
        print(f"[!] Cannot read {file_path}: {e}")
        return None

# ============================================================
# FUNCTION 2: Collect all files in a folder
# ============================================================
def collect_files(folder):
    """Walk through folder and return list of all file paths."""
    all_files = []
    # os.walk goes into every sub-folder
    for root, dirs, files in os.walk(folder):
        # Skip hidden folders like .git
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for name in files:
            # Skip our own baseline file so we don't hash it
            if name == BASELINE_FILE:
                continue
            # Join folder + filename to get full path
            all_files.append(os.path.join(root, name))
    return all_files

# ============================================================
# FUNCTION 3: Create baseline - save original fingerprints
# ============================================================
def create_baseline(folder):
    """Create baseline.json with hashes of all files in folder."""
    print(f"[*] Creating baseline for folder: {folder}")
    baseline = {}
    files = collect_files(folder)

    # Loop through each file, hash it, save it
    for file_path in files:
        file_hash = get_file_hash(file_path)
        if file_hash:
            # Use relative path so baseline works on any computer
            rel_path = os.path.relpath(file_path, folder)
            baseline[rel_path] = file_hash
            print(f"  [+] Added: {rel_path}")

    # Save baseline to JSON file
    with open(os.path.join(folder, BASELINE_FILE), "w") as f:
        json.dump(baseline, f, indent=4)

    print(f"[+] Baseline created! {len(baseline)} files saved in {BASELINE_FILE}")
    print("[*] Keep this file safe. It is your original record.")

# ============================================================
# FUNCTION 4: Scan and compare - check for changes
# ============================================================
def scan_folder(folder):
    """Compare current files with baseline and report changes."""
    baseline_path = os.path.join(folder, BASELINE_FILE)

    # Check if baseline exists first
    if not os.path.exists(baseline_path):
        print(f"[!] No baseline found! Run first: python integrity_monitor.py --init --folder {folder}")
        sys.exit(1)

    # Load old baseline
    with open(baseline_path, "r") as f:
        baseline = json.load(f)

    print(f"[*] Scanning folder: {folder}")
    print(f"[*] Baseline has {len(baseline)} files. Checking...")

    # Get current files
    current_files = collect_files(folder)
    current = {}

    for file_path in current_files:
        file_hash = get_file_hash(file_path)
        if file_hash:
            rel_path = os.path.relpath(file_path, folder)
            current[rel_path] = file_hash

    # Counters for report
    changed = []
    added = []
    deleted = []

    # Check 1: Files that changed or were deleted
    for path, old_hash in baseline.items():
        if path not in current:
            deleted.append(path)  # File was deleted
        elif current[path] != old_hash:
            changed.append(path)  # Hash different = file changed

    # Check 2: New files added
    for path in current:
        if path not in baseline:
            added.append(path)

    # ============================================================
    # PRINT REPORT - This is what user sees
    # ============================================================
    print("\n========== INTEGRITY REPORT ==========")
    if not changed and not added and not deleted:
        print("[✓] All files are SAFE. No changes detected.")
    else:
        if changed:
            print(f"\n[!] MODIFIED ({len(changed)} files):")
            for p in changed:
                print(f"  - {p}")

        if added:
            print(f"\n[+] NEW FILES ADDED ({len(added)} files):")
            for p in added:
                print(f"  - {p}")

        if deleted:
            print(f"\n[-] DELETED ({len(deleted)} files):")
            for p in deleted:
                print(f"  - {p}")

    print("======================================")
    print("Scan complete.")

# ============================================================
# MAIN - This runs when you type python integrity_monitor.py
# ============================================================
def main():
    # Set up commands: --init to create baseline, --scan to check
    parser = argparse.ArgumentParser(description="File Integrity Monitor by Batholomew Okoro")
    parser.add_argument("--folder", required=True, help="Folder to monitor, e.g. --folder ./my_files")
    parser.add_argument("--init", action="store_true", help="Create baseline (first time only)")
    parser.add_argument("--scan", action="store_true", help="Scan and compare with baseline")

    args = parser.parse_args()

    # Check folder exists
    if not os.path.isdir(args.folder):
        print(f"[!] Folder not found: {args.folder}")
        sys.exit(1)

    # Decide what to do
    if args.init:
        create_baseline(args.folder)
    elif args.scan:
        scan_folder(args.folder)
    else:
        print("[!] Please use --init or --scan")
        print("Example: python integrity_monitor.py --init --folder ./test_folder")
        print("Example: python integrity_monitor.py --scan --folder ./test_folder")

# Run main only if this file is run directly
if __name__ == "__main__":
    main()