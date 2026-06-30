from __future__ import annotations
from dataclasses import dataclass, field
from fnmatch import fnmatch


@dataclass
class FileEntry:
    path: str
    text: str | None
    size: int
    is_binary: bool


@dataclass
class FileTree:
    root_name: str
    entries: list[FileEntry] = field(default_factory=list)

    def get(self, path: str) -> FileEntry | None:
        for e in self.entries:
            if e.path == path:
                return e
        return None

    def match(self, glob: str) -> list[FileEntry]:
        return [
            e
            for e in self.entries
            if fnmatch(e.path, glob) or fnmatch(e.path.split("/")[-1], glob)
        ]

    def text_files(self) -> list[FileEntry]:
        return [e for e in self.entries if e.text is not None]
