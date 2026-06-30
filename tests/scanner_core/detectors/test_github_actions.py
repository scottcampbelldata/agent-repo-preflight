from agent_repo_preflight.scanner_core.filetree import FileTree, FileEntry
from agent_repo_preflight.scanner_core.detectors.github_actions import (
    GitHubActionsDetector,
)


def _wf(content):
    return FileTree("r", [FileEntry(".github/workflows/ci.yml", content, len(content), False)])


def test_write_all_and_unpinned():
    wf = "permissions: write-all\njobs:\n  b:\n    steps:\n      - uses: actions/checkout@v4\n"
    types = {f.type for f in GitHubActionsDetector().detect(_wf(wf))}
    assert "ci.write_all_permissions" in types
    assert "ci.unpinned_action" in types


def test_pinned_sha_not_flagged():
    wf = "jobs:\n  b:\n    steps:\n      - uses: actions/checkout@" + "a" * 40 + "\n"
    types = {f.type for f in GitHubActionsDetector().detect(_wf(wf))}
    assert "ci.unpinned_action" not in types


def test_pull_request_target():
    wf = "on: pull_request_target\njobs: {}\n"
    types = {f.type for f in GitHubActionsDetector().detect(_wf(wf))}
    assert "ci.pull_request_target" in types
