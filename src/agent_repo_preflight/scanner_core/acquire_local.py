from __future__ import annotations

import os

from .filetree import FileEntry, FileTree

_SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build"}


def _decode(data: bytes) -> tuple[str | None, bool]:
    if b"\x00" in data:
        return None, True
    try:
        return data.decode("utf-8"), False
    except UnicodeDecodeError:
        try:
            return data.decode("latin-1"), False
        except UnicodeDecodeError:
            return None, True


def load_local(path: str, *, max_files: int = 5000, max_file_bytes: int = 1_000_000) -> FileTree:
    root = os.path.abspath(path)
    root_name = os.path.basename(root.rstrip(os.sep)) or root
    entries: list[FileEntry] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS]
        for fn in filenames:
            if len(entries) >= max_files:
                return FileTree(root_name, entries)
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, root).replace(os.sep, "/")
            try:
                size = os.path.getsize(full)
            except OSError:
                continue
            if size > max_file_bytes:
                entries.append(FileEntry(rel, None, size, False))
                continue
            try:
                with open(full, "rb") as fh:
                    data = fh.read()
            except OSError:
                continue
            text, is_binary = _decode(data)
            entries.append(FileEntry(rel, text, size, is_binary))
    return FileTree(root_name, entries)
