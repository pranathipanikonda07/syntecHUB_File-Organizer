"""Demo/test harness for file_organizer

Creates a temporary directory with sample files and demonstrates dry-run and real-run
behaviour of the file_organizer module.
"""
from pathlib import Path
import tempfile
import shutil
import os

from file_organizer import organize_directory


def create_sample_files(base: Path) -> None:
    base.mkdir(parents=True, exist_ok=True)
    sample = [
        "cat.jpg",
        "dog.JPG",
        "report.pdf",
        "archive.tar.gz",
        "README",
        "notes.txt",
        "stuff (1).txt",
    ]

    for name in sample:
        (base / name).write_text(f"sample: {name}")


def demo():
    tmp = Path(tempfile.mkdtemp(prefix="file-organizer-demo-"))
    try:
        print("Created demo dir:", tmp)
        create_sample_files(tmp)

        print("Dry-run (no file moves):")
        organize_directory(tmp, recursive=False, dry_run=True, log_file=None)

        print("Actual run (moving files):")
        organize_directory(tmp, recursive=False, dry_run=False, log_file=None)

        print("Resulting tree:")
        for p in sorted(tmp.rglob("*")):
            print(p.relative_to(tmp))

    finally:
        print("Cleaning up demo directory")
        shutil.rmtree(tmp)


if __name__ == "__main__":
    demo()
