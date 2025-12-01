#!/usr/bin/env python3
"""
file_organizer.py

Scans a folder and moves files into subfolders based on file extension.

Features:
- Uses os and shutil
- Handles name collisions (suffixing with number)
- Supports dry-run mode and detailed logging
- Optional recursion

Usage examples:
    python file_organizer.py /path/to/scan --dry-run
    python file_organizer.py C:\Users\You\Downloads --log-file organizer.log

"""
from __future__ import annotations

import argparse
import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional, Tuple


LOG = logging.getLogger("file_organizer")


def setup_logging(log_file: Optional[Path] = None, verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    handlers = [logging.StreamHandler()]
    if log_file:
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=handlers,
    )


def get_files_to_move(root: Path, recursive: bool) -> Iterable[Path]:
    if recursive:
        for p in root.rglob("*"):
            if p.is_file():
                yield p
    else:
        for p in root.iterdir():
            if p.is_file():
                yield p


def extension_folder_name(ext: str) -> str:
    """Return a folder name for an extension like '.jpg' -> 'jpg' or empty -> 'no_extension'."""
    if not ext:
        return "no_extension"
    return ext.lower().lstrip(".")


def unique_destination(dest: Path) -> Path:
    """If dest exists, generate a unique destination path by adding a numeric suffix.

    Examples:
        file.txt -> file(1).txt -> file(2).txt
    """
    if not dest.exists():
        return dest

    stem = dest.stem
    suffix = dest.suffix
    parent = dest.parent

    idx = 1
    while True:
        candidate = parent / f"{stem}({idx}){suffix}"
        if not candidate.exists():
            return candidate
        idx += 1


def move_file(src: Path, dest_dir: Path, dry_run: bool = False) -> Tuple[Path, str]:
    """Move a file `src` into directory `dest_dir`, resolving collisions.

    Returns tuple (final_dest_path, action_description)
    """
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / src.name
    final_dest = unique_destination(dest)

    if dry_run:
        LOG.info("DRY-RUN: Would move %s -> %s", src, final_dest)
        return final_dest, "dry-run"

    shutil.move(str(src), str(final_dest))
    LOG.info("Moved %s -> %s", src, final_dest)
    return final_dest, "moved"


def organize_directory(
    target: Path,
    recursive: bool = False,
    dry_run: bool = False,
    log_file: Optional[Path] = None,
    keep_top_level: bool = True,
) -> int:
    """Organize files inside target directory by extension.

    - If keep_top_level is True, files are moved into subfolders inside `target`.
    - If False and recursive, e.g. for each subdir we create extension-folders within that subdir

    Returns number of files moved (or would be moved if dry-run).
    """
    setup_logging(log_file, verbose=False)

    if not target.is_dir():
        LOG.error("Target is not a directory: %s", target)
        return 0

    moved_count = 0

    files = list(get_files_to_move(target, recursive=recursive))
    LOG.info("Found %d files to process (recursive=%s)", len(files), recursive)

    for f in files:
        ext = f.suffix
        folder_name = extension_folder_name(ext)

        if keep_top_level:
            dest_dir = target / folder_name
        else:
            # place under the file's current parent directory
            dest_dir = f.parent / folder_name

        final_dest, action = move_file(f, dest_dir, dry_run=dry_run)
        if action in ("moved", "dry-run"):
            moved_count += 1

    LOG.info("Completed. Files processed: %d (dry_run=%s)", moved_count, dry_run)
    return moved_count


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Scan a folder and move files into extension-based subfolders")
    p.add_argument("target", type=Path, help="Target directory to scan")
    p.add_argument("--recursive", action="store_true", help="Recurse into subdirectories")
    p.add_argument("--dry-run", action="store_true", help="Do not move files; only show what would be done")
    p.add_argument("--log-file", type=Path, default=Path.cwd() / "file_organizer.log", help="Path to a logfile")
    p.add_argument("--no-top-level", dest="keep_top_level", action="store_false", help="When recursive, keep extension folders next to each file instead of at top level")
    p.add_argument("--verbose", action="store_true", help="Verbose logging (debug)")
    return p.parse_args()


def main() -> None:
    args = parse_args()

    setup_logging(args.log_file, verbose=args.verbose)
    LOG.debug("Arguments: %s", args)

    try:
        count = organize_directory(
            args.target, recursive=args.recursive, dry_run=args.dry_run, log_file=args.log_file, keep_top_level=args.keep_top_level
        )
    except Exception as exc:  # broad catch for automation scripts so users get a message
        LOG.exception("Error during organizing: %s", exc)
        raise

    if args.dry_run:
        LOG.info("Dry-run: %d files would be moved", count)
    else:
        LOG.info("Success: %d files moved", count)


if __name__ == "__main__":
    main()
