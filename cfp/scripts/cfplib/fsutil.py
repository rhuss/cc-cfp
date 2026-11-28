"""File system helpers shared by cfplib modules."""

import os
import stat
from pathlib import Path


def write_text_atomic(path, text):
    """Write ``text`` atomically: a hidden sibling temp file is synced and renamed over the target.

    A symlinked target is resolved first so the real file receives the write
    and the link survives. An existing file keeps its mode. Returns the path
    that was written (the link target for a symlink).
    """
    path = Path(path)
    if path.is_symlink():
        path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with open(temp, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        if path.exists():
            os.chmod(temp, stat.S_IMODE(path.stat().st_mode))
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()
    return path
