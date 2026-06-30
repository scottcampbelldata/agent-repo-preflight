import io
import tarfile

import pytest

from agent_repo_preflight.scanner_core.acquire_remote import (
    load_remote,
    load_tarball_bytes,
    parse_github_url,
    tarball_url,
)


def _make_tarball():
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for name, content in [
            ("org-repo-abc123/README.md", b"hi"),
            ("org-repo-abc123/src/x.py", b"print(1)"),
        ]:
            info = tarfile.TarInfo(name)
            info.size = len(content)
            tar.addfile(info, io.BytesIO(content))
    return buf.getvalue()


def test_parse_github_url():
    assert parse_github_url("https://github.com/org/repo") == ("org", "repo", None)
    assert parse_github_url("https://github.com/org/repo/tree/main") == (
        "org",
        "repo",
        "main",
    )
    with pytest.raises(ValueError):
        parse_github_url("https://gitlab.com/org/repo")


def test_tarball_url():
    assert tarball_url("org", "repo") == "https://codeload.github.com/org/repo/tar.gz/HEAD"
    assert tarball_url("org", "repo", "main") == "https://codeload.github.com/org/repo/tar.gz/main"


def test_load_tarball_strips_root_component():
    tree = load_tarball_bytes(_make_tarball(), "repo")
    assert {e.path for e in tree.entries} == {"README.md", "src/x.py"}
    assert tree.get("README.md").text == "hi"


def test_load_remote_uses_injected_fetch():
    data = _make_tarball()
    tree = load_remote("https://github.com/org/repo", fetch=lambda url: data)
    assert tree.get("src/x.py").text == "print(1)"
