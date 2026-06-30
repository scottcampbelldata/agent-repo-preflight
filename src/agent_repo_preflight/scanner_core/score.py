from __future__ import annotations

from .findings import Finding

SEVERITY_WEIGHT = {"info": 0, "low": 1, "medium": 4, "high": 8, "critical": 16}
CAPS = ["filesystem", "network", "secrets", "shell", "install_hooks", "ci"]


def score(findings: list[Finding]) -> int:
    return sum(SEVERITY_WEIGHT.get(f.severity, 0) for f in findings)


def verdict(findings: list[Finding]) -> str:
    for f in findings:
        if f.severity == "critical":
            return "FAIL"
        if f.category == "install-hooks" and "network" in f.blast_radius:
            return "FAIL"
    if any(f.severity in ("high", "medium") for f in findings):
        return "REVIEW"
    return "PASS"


def _rank(sev: str) -> str:
    if sev in ("critical", "high"):
        return "HIGH"
    if sev == "medium":
        return "MED"
    if sev == "low":
        return "LOW"
    return "NONE"


_ORDER = {"NONE": 0, "LOW": 1, "MED": 2, "HIGH": 3}


def blast_radius_rollup(findings: list[Finding]) -> dict[str, str]:
    roll = {cap: "NONE" for cap in CAPS}
    for f in findings:
        for cap in f.blast_radius:
            if cap in roll and _ORDER[_rank(f.severity)] > _ORDER[roll[cap]]:
                roll[cap] = _rank(f.severity)
    return roll
