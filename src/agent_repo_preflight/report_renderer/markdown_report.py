from __future__ import annotations
from ..scanner_core.model import ReportModel

_VERDICT_LINE = {
    "PASS": "✅ PASS — no blocking risk indicators found",
    "REVIEW": "⚠️ REVIEW — human review recommended before agent use",
    "FAIL": "⛔ FAIL — human review required before agent use",
}


def render_markdown(report: ReportModel) -> str:
    r = report
    lines = [
        f"# AI-Agent Preflight: {r.verdict}",
        "",
        _VERDICT_LINE.get(r.verdict, r.verdict),
        "",
        f"**Repo:** `{r.repo['name']}` ({r.repo['source']})  ",
        f"**Risk score:** {r.score}",
        "",
        "## Blast radius",
        "",
        "| Capability | Level |",
        "|---|---|",
    ]
    for cap, level in r.blast_radius.items():
        lines.append(f"| {cap} | {level} |")
    lines += ["", "## Findings", ""]
    if r.findings:
        lines += ["| Severity | Rule | File:Line | Evidence |", "|---|---|---|---|"]
        for f in r.findings:
            ev = f.evidence.replace("|", "\\|")[:80]
            lines.append(
                f"| {f.severity.upper()} | {f.rule_id} | `{f.file}:{f.line}` | `{ev}` |"
            )
    else:
        lines.append("_No findings._")
    if r.agent_instructions:
        lines += ["", "## Agent instruction surfaces", ""]
        for ai in r.agent_instructions:
            lines.append(f"- **{ai['surface']}** — `{ai['file']}`")
    if r.chains:
        lines += ["", "## Suspicious setup chains (heuristic)", ""]
        for c in r.chains:
            lines.append(
                " → ".join(f"{s.kind} (`{s.file}:{s.line}`)" for s in c.steps)
            )
    lines += ["", "---", f"_{r.disclaimer}_"]
    return "\n".join(lines)
