import pytest

from agent_repo_preflight.scanner_core.rules import SEVERITIES, RuleError, load_rules


def test_load_valid_rule(tmp_path):
    (tmp_path / "r.yaml").write_text(
        "id: x\nname: X\nseverity: high\ncategory: install-hooks\n"
        "blast_radius: [network]\nmatch:\n  facts: [pkg.lifecycle_script]\n"
        "  patterns: ['curl']\nexplanation: e\nremediation: r\n",
        encoding="utf-8",
    )
    rules = load_rules(str(tmp_path))
    assert len(rules) == 1
    r = rules[0]
    assert r.id == "x" and r.severity == "high" and r.match["facts"] == ["pkg.lifecycle_script"]


def test_invalid_severity_raises(tmp_path):
    (tmp_path / "bad.yaml").write_text(
        "id: y\nname: Y\nseverity: explosive\ncategory: c\nmatch: {}\n"
        "explanation: e\nremediation: r\n",
        encoding="utf-8",
    )
    with pytest.raises(RuleError):
        load_rules(str(tmp_path))


def test_packaged_rules_load_and_are_unique():
    rules = load_rules()  # default packaged dir
    assert len(rules) >= 20
    ids = [r.id for r in rules]
    assert len(ids) == len(set(ids))
    assert all(r.severity in SEVERITIES for r in rules)
