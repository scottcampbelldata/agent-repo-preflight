from agent_repo_preflight.scanner_core.chains import build_chains
from agent_repo_preflight.scanner_core.facts import Fact
from agent_repo_preflight.scanner_core.filetree import FileEntry, FileTree


def test_builds_chain_from_postinstall_to_script_fetch():
    tree = FileTree(
        "r",
        [
            FileEntry("README.md", "Run npm install to set up.", 20, False),
            FileEntry("package.json", "{}", 2, False),
            FileEntry("scripts/setup.js", "fetch('http://x'); eval(atob(s))", 30, False),
        ],
    )
    facts = [
        Fact(
            "pkg.lifecycle_script",
            "package.json",
            3,
            {"hook": "postinstall", "command": "node scripts/setup.js"},
            evidence="node scripts/setup.js",
        ),
        Fact(
            "content.base64_exec",
            "scripts/setup.js",
            1,
            {"pattern_id": "base64_exec"},
            evidence="eval(atob(s))",
        ),
    ]
    chains = build_chains(facts, tree)
    assert chains, "expected at least one chain"
    kinds = [s.kind for s in chains[0].steps]
    assert "lifecycle_hook" in kinds and "referenced_script" in kinds


def test_no_chain_returns_empty():
    assert build_chains([], FileTree("r", [])) == []
