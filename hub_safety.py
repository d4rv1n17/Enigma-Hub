"""Filesystem checks shared by the product manager and Hub installer."""
from pathlib import Path
import stat


def reject_reparse(path):
    """Reject links and Windows junctions in a target or any existing ancestor."""
    path = Path(path).absolute()
    for entry in (path, *path.parents):
        try:
            info = entry.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise ValueError("Choose a regular folder without links or junctions.")
