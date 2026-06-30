from agent_repo_preflight.scanner_core.acquire_local import load_local


def test_load_local_reads_text_and_flags_binary(tmp_path):
    (tmp_path / "a.txt").write_text("hello", encoding="utf-8")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "b.py").write_text("print(1)", encoding="utf-8")
    (tmp_path / "img.bin").write_bytes(b"\x00\x01\x02\x03")
    tree = load_local(str(tmp_path))
    assert tree.get("a.txt").text == "hello"
    assert tree.get("sub/b.py").text == "print(1)"
    assert tree.get("img.bin").is_binary is True
    assert tree.get("img.bin").text is None
    assert {e.path for e in tree.text_files()} == {"a.txt", "sub/b.py"}


def test_load_local_skips_git_and_respects_caps(tmp_path):
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_text("x", encoding="utf-8")
    (tmp_path / "big.txt").write_text("y" * 50, encoding="utf-8")
    tree = load_local(str(tmp_path), max_file_bytes=10)
    assert tree.get(".git/config") is None  # .git always skipped
    big = tree.get("big.txt")
    assert (
        big.is_binary is False and big.text is None and big.size == 50
    )  # oversized: recorded, not read
