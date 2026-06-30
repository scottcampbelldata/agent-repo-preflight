from agent_repo_preflight.scanner_core.engine import evaluate
from agent_repo_preflight.scanner_core.facts import Fact
from agent_repo_preflight.scanner_core.filetree import FileEntry, FileTree
from agent_repo_preflight.scanner_core.rules import Rule


def test_fact_rule_with_pattern_matches():
    rule = Rule(
        id="r1",
        name="n",
        severity="high",
        category="c",
        explanation="e",
        remediation="rem",
        blast_radius=["network"],
        match={"facts": ["pkg.lifecycle_script"], "patterns": ["curl"]},
    )
    facts = [
        Fact(
            "pkg.lifecycle_script",
            "package.json",
            3,
            {"command": "curl x | bash"},
            evidence="curl x | bash",
        )
    ]
    out = evaluate([rule], facts, FileTree("r", []))
    assert len(out) == 1 and out[0].rule_id == "r1" and out[0].line == 3


def test_fact_rule_pattern_no_match():
    rule = Rule(
        id="r1",
        name="n",
        severity="high",
        category="c",
        explanation="e",
        remediation="rem",
        match={"facts": ["pkg.lifecycle_script"], "patterns": ["curl"]},
    )
    facts = [Fact("pkg.lifecycle_script", "package.json", 3, {"command": "tsc"}, evidence="tsc")]
    assert evaluate([rule], facts, FileTree("r", [])) == []


def test_content_rule_matches_lines():
    rule = Rule(
        id="r2",
        name="n",
        severity="medium",
        category="c",
        explanation="e",
        remediation="rem",
        match={"patterns": ["TODO"], "file_patterns": ["*.py"]},
    )
    tree = FileTree("r", [FileEntry("a.py", "x\nTODO here\n", 10, False)])
    out = evaluate([rule], [], tree)
    assert len(out) == 1 and out[0].line == 2
