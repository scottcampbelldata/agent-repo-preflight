from agent_repo_preflight.scanner_core.findings import Finding
from agent_repo_preflight.scanner_core.refine import downgrade_documentation_findings


def _f(file, severity="high", category="dangerous-commands"):
    return Finding("r", severity, category, file, 1, "ev", "explain", "rem", ["shell"])


def test_doc_file_dangerous_finding_is_downgraded():
    out = downgrade_documentation_findings([_f("README.md", "critical")])
    assert out[0].severity == "low"
    assert "documentation" in out[0].explanation.lower()


def test_non_doc_file_is_unchanged():
    out = downgrade_documentation_findings([_f("scripts/install.sh", "critical")])
    assert out[0].severity == "critical"


def test_agent_instruction_in_markdown_is_not_downgraded():
    # CLAUDE.md is markdown, but agents genuinely act on it — keep its severity.
    out = downgrade_documentation_findings([_f("CLAUDE.md", "high", category="agent-instructions")])
    assert out[0].severity == "high"


def test_low_and_info_doc_findings_untouched():
    out = downgrade_documentation_findings([_f("README.md", "low"), _f("docs/x.md", "info")])
    assert [f.severity for f in out] == ["low", "info"]


def test_test_fixture_dangerous_finding_is_downgraded():
    # A dangerous-looking string in a test fixture is not a setup-execution risk.
    out = downgrade_documentation_findings(
        [_f("tests/test_requests.py", "high", category="secrets")]
    )
    assert out[0].severity == "low"
    assert "test" in out[0].explanation.lower()


def test_various_test_path_conventions_downgraded():
    for path in ("test_foo.py", "src/foo.test.js", "spec/foo_spec.rb", "app/__tests__/x.ts"):
        out = downgrade_documentation_findings([_f(path, "high", category="dangerous-commands")])
        assert out[0].severity == "low", path


def test_real_source_file_not_downgraded():
    out = downgrade_documentation_findings([_f("src/setup.js", "critical")])
    assert out[0].severity == "critical"
