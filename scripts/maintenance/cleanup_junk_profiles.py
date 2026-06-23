"""
cleanup_junk_profiles.py
========================
Scans the PP & Uo Note Dummy directory and deletes profile files (.docx) whose
"Name of Person" field is NOT a valid person name (place names, report jargon,
single common words, etc.).

Also deletes the matching UO note and any *_review.docx* files for the same name.

Usage
-----
    python cleanup_junk_profiles.py            # dry-run (shows what would be deleted)
    python cleanup_junk_profiles.py --delete   # actually deletes the files
"""

import os
import re
import sys
import argparse

# ---------------------------------------------------------------------------
# Ensure project root and modules are on the path
# ---------------------------------------------------------------------------
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, base_dir)
sys.path.insert(0, os.path.join(base_dir, "backend"))

from app.infrastructure.neo4j.graph_db import _is_valid_person_name
from app.infrastructure.documents.utils import load_profile_database, PersonProfile

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PP_DIR = os.path.join(
    BASE_DIR,
    "PP & Uo Note Dummy-20260427T091522Z-3-001",
    "PP & Uo Note Dummy",
)


def find_uo_note(profile_name: str, profile_num: str) -> str | None:
    """Return the path to the UO note that corresponds to this profile, if it exists."""
    if not os.path.isdir(PP_DIR):
        return None
    if profile_num:
        pattern = r"^" + re.escape(profile_num) + r"\D.*uo"
        for fname in os.listdir(PP_DIR):
            if re.match(pattern, fname, re.IGNORECASE):
                return os.path.join(PP_DIR, fname)
    first_word = profile_name.lower().split()[0] if profile_name else ""
    if len(first_word) >= 3:
        for fname in os.listdir(PP_DIR):
            flower = fname.lower()
            if "uo" in flower and first_word in flower:
                return os.path.join(PP_DIR, fname)
    return None


def find_review_files(profile_name: str) -> list:
    """Return any *_review.docx* files whose stem matches the profile name."""
    results = []
    if not profile_name or not os.path.isdir(PP_DIR):
        return results
    safe_name = re.sub(r'[<>:"/\\|?*]', '_', profile_name)
    review_path = os.path.join(PP_DIR, f"{safe_name}_review.docx")
    if os.path.exists(review_path):
        results.append(review_path)
    return results


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    parser = argparse.ArgumentParser(
        description="Clean up junk PP profiles with invalid person names."
    )
    parser.add_argument(
        "--delete",
        action="store_true",
        help="Actually delete the files (default is dry-run only)",
    )
    args = parser.parse_args()

    dry_run = not args.delete

    if dry_run:
        print("=== DRY RUN — no files will be deleted ===")
        print("Run with --delete to actually remove files.\n")
    else:
        print("=== LIVE DELETE MODE ===\n")

    if not os.path.isdir(PP_DIR):
        print(f"[Error] PP directory not found: {PP_DIR}")
        sys.exit(1)

    profiles = load_profile_database(PP_DIR)
    print(f"Loaded {len(profiles)} profiles from PP directory.\n")

    junk_profiles = []
    valid_profiles = []

    for prof in profiles:
        name = prof.name.strip()
        if not name:
            # No name field at all — treat as junk
            junk_profiles.append(prof)
        elif _is_valid_person_name(name):
            valid_profiles.append(prof)
        else:
            junk_profiles.append(prof)

    print(f"Valid profiles : {len(valid_profiles)}")
    print(f"Junk profiles  : {len(junk_profiles)}")
    print()

    deleted_count = 0
    skipped_count = 0

    for prof in junk_profiles:
        name = prof.name or "(no name)"
        files_to_delete = [prof.filepath]

        # Find associated UO note
        profile_num = re.match(r"^(\d+)", prof.filename)
        num_str = profile_num.group(1) if profile_num else ""
        uo = find_uo_note(name, num_str)
        if uo and os.path.exists(uo):
            files_to_delete.append(uo)

        # Find review files
        files_to_delete.extend(find_review_files(name))

        print(f"  [JUNK] '{name}' ({prof.filename})")
        for fpath in files_to_delete:
            rel = os.path.relpath(fpath, PP_DIR)
            if dry_run:
                print(f"    Would delete: {rel}")
            else:
                try:
                    os.remove(fpath)
                    print(f"    Deleted: {rel}")
                    deleted_count += 1
                except Exception as e:
                    print(f"    [Warning] Could not delete {rel}: {e}")
                    skipped_count += 1

    # Also clean all *_review.docx* files in the PP directory regardless of matching profile
    print("\n--- Scanning for leftover *_review.docx files ---")
    for fname in os.listdir(PP_DIR):
        if fname.lower().endswith("_review.docx"):
            fpath = os.path.join(PP_DIR, fname)
            if dry_run:
                print(f"  Would delete review file: {fname}")
            else:
                try:
                    os.remove(fpath)
                    print(f"  Deleted review file: {fname}")
                    deleted_count += 1
                except Exception as e:
                    print(f"  [Warning] Could not delete {fname}: {e}")
                    skipped_count += 1

    print()
    if dry_run:
        print(f"=== Dry run complete. {len(junk_profiles)} junk profile(s) identified. ===")
        print("Run with --delete to remove them.")
    else:
        print(f"=== Cleanup complete. {deleted_count} file(s) deleted, {skipped_count} skipped. ===")


if __name__ == "__main__":
    main()
