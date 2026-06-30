from agent_repo_preflight.scanner_core.score import (
    score,
    verdict,
    blast_radius_rollup,
    SEVERITY_WEIGHT,
)
from agent_repo_preflight.scanner_core.findings import Finding


def _f(sev, cat="c", blast=None):
    return Finding("r", sev, cat, "f", 1, "e", "ex", "rem", blast or [])


def test_verdict_fail_on_critical():
    assert verdict([_f("critical")]) == "FAIL"


def test_verdict_fail_on_install_network():
    assert verdict([_f("medium", cat="install-hooks", blast=["network"])]) == "FAIL"


def test_verdict_review_and_pass():
    assert verdict([_f("high")]) == "REVIEW"
    assert verdict([_f("low")]) == "PASS"
    assert verdict([]) == "PASS"


def test_score_sums_weights():
    assert score([_f("high"), _f("low")]) == SEVERITY_WEIGHT["high"] + SEVERITY_WEIGHT["low"]


def test_blast_rollup():
    roll = blast_radius_rollup([_f("high", blast=["network"]), _f("low", blast=["ci"])])
    assert roll["network"] == "HIGH" and roll["ci"] == "LOW" and roll["secrets"] == "NONE"
