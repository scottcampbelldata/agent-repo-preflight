from __future__ import annotations
import re
from .findings import Finding

# Documentation/non-executable file types. Content here is read by humans, not
# auto-executed when an AI agent installs/builds/runs the repo.
_DOC_EXT = (".md", ".markdown", ".rst", ".txt", ".adoc", ".rdoc")

# Test files. Dangerous-looking strings in test fixtures/mocks (URLs, paths like
# /etc/passwd, sample payloads) are pervasive and benign; they are not install-time
# execution. Detected by common path/name conventions across ecosystems.
_TEST_PATTERNS = (
    re.compile(r"(^|/)tests?/"),
    re.compile(r"(^|/)__tests__/"),
    re.compile(r"(^|/)specs?/"),
    re.compile(r"(^|/)test_[^/]+$"),
    re.compile(r"_test\.[a-z0-9]+$"),
    re.compile(r"\.(test|spec)\.[a-z0-9]+$"),
    re.compile(r"_spec\.[a-z0-9]+$"),
)

_DOC_NOTE = " [Match is in a documentation file, which is not auto-executed during agent setup.]"
_TEST_NOTE = " [Match is in a test file, which is not auto-executed during agent setup.]"


def _is_doc(path: str) -> bool:
    return path.lower().endswith(_DOC_EXT)


def _is_test(path: str) -> bool:
    p = path.lower()
    return any(rx.search(p) for rx in _TEST_PATTERNS)


def downgrade_documentation_findings(findings: list[Finding]) -> list[Finding]:
    """Cap the severity of blocking findings in non-setup-executed files.

    Documentation and test files are not run automatically when an AI agent
    installs/builds a repo, so a dangerous pattern there is informational rather
    than a setup-execution risk. Such findings are downgraded to ``low`` (still
    shown, but non-blocking) with an explanatory note.

    Agent-instruction findings are exempt: agents genuinely act on files like
    CLAUDE.md regardless of extension, so those keep their assigned severity.

    Tradeoff: a payload deliberately hidden under a ``tests/`` path is downgraded,
    not suppressed — it still appears as a low finding. Install-hook, CI, and
    agent-instruction findings are never downgraded, so the common auto-execution
    vectors keep full severity. This is a triage tool, not a safety guarantee.
    """
    for f in findings:
        if f.category == "agent-instructions":
            continue
        if f.severity not in ("critical", "high", "medium"):
            continue
        if _is_doc(f.file):
            f.severity = "low"
            if _DOC_NOTE not in f.explanation:
                f.explanation += _DOC_NOTE
        elif _is_test(f.file):
            f.severity = "low"
            if _TEST_NOTE not in f.explanation:
                f.explanation += _TEST_NOTE
    return findings
