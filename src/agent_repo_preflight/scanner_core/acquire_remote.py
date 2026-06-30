from __future__ import annotations

import io
import tarfile
import zlib
from urllib.parse import urlparse

from .acquire_local import _decode
from .filetree import FileEntry, FileTree


def _gunzip_capped(data: bytes, max_out: int) -> bytes:
    """Decompress gzip data, aborting if the output exceeds max_out bytes.

    Guards against decompression ("zip") bombs: a tiny gzip can otherwise expand to
    many gigabytes and exhaust memory. Streams the output and caps it absolutely.
    """
    d = zlib.decompressobj(16 + zlib.MAX_WBITS)  # 16 => gzip header
    out = bytearray()
    buf = data
    while buf:
        out += d.decompress(buf, 1 << 20)  # at most 1 MiB produced per call
        if len(out) > max_out:
            raise ValueError("Decompressed tarball exceeds cap (possible zip bomb)")
        buf = d.unconsumed_tail
    out += d.flush()
    if len(out) > max_out:
        raise ValueError("Decompressed tarball exceeds cap (possible zip bomb)")
    return bytes(out)


def parse_github_url(url: str) -> tuple[str, str, str | None]:
    p = urlparse(url)
    if p.netloc not in ("github.com", "www.github.com"):
        raise ValueError(f"Not a GitHub URL: {url}")
    parts = [s for s in p.path.split("/") if s]
    if len(parts) < 2:
        raise ValueError(f"URL missing owner/repo: {url}")
    owner, repo = parts[0], parts[1].removesuffix(".git")
    ref = None
    if len(parts) >= 4 and parts[2] in ("tree", "commit"):
        ref = parts[3]
    return owner, repo, ref


def tarball_url(owner: str, repo: str, ref: str | None = None) -> str:
    return f"https://codeload.github.com/{owner}/{repo}/tar.gz/{ref or 'HEAD'}"


def load_tarball_bytes(
    data: bytes,
    root_name: str,
    *,
    max_files: int = 5000,
    max_file_bytes: int = 1_000_000,
    max_decompressed: int = 500_000_000,
) -> FileTree:
    raw = _gunzip_capped(data, max_decompressed)
    entries: list[FileEntry] = []
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:") as tar:
        for member in tar.getmembers():
            if not member.isfile() or len(entries) >= max_files:
                continue
            rel = member.name.split("/", 1)[1] if "/" in member.name else member.name
            if not rel:
                continue
            if member.size > max_file_bytes:
                entries.append(FileEntry(rel, None, member.size, False))
                continue
            f = tar.extractfile(member)
            payload = f.read() if f else b""
            text, is_binary = _decode(payload)
            entries.append(FileEntry(rel, text, member.size, is_binary))
    return FileTree(root_name, entries)


def _default_fetch(url: str) -> bytes:
    import os

    import requests

    headers = {"User-Agent": "agent-repo-preflight"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    resp = requests.get(url, headers=headers, timeout=30, stream=True, allow_redirects=True)
    resp.raise_for_status()
    chunks, total = [], 0
    for chunk in resp.iter_content(8192):
        total += len(chunk)
        if total > 50_000_000:
            raise ValueError("Repository tarball exceeds 50 MB cap")
        chunks.append(chunk)
    return b"".join(chunks)


def load_remote(url: str, *, fetch=_default_fetch, **kw) -> FileTree:
    owner, repo, ref = parse_github_url(url)
    data = fetch(tarball_url(owner, repo, ref))
    return load_tarball_bytes(data, repo, **kw)
