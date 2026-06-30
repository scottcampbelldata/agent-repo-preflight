import os

import pytest

from agent_repo_preflight.scanner_core.acquire_local import load_local
from agent_repo_preflight.scanner_core.scan import scan_tree

EX = os.path.join(os.path.dirname(os.path.dirname(__file__)), "examples")


def _verdict(name):
    tree = load_local(os.path.join(EX, name))
    return scan_tree(tree, source=f"local:{name}", scanned_at="t").verdict


def test_clean_passes():
    assert _verdict("clean") == "PASS"


@pytest.mark.parametrize("name", ["suspicious-node", "suspicious-python", "suspicious-mcp"])
def test_suspicious_repos_flagged(name):
    assert _verdict(name) in ("REVIEW", "FAIL")


def test_suspicious_node_is_fail():
    assert _verdict("suspicious-node") == "FAIL"
