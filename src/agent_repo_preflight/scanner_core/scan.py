from __future__ import annotations

import os

from .acquire_local import load_local
from .acquire_remote import load_remote, parse_github_url
from .chains import build_chains
from .detectors import (  # noqa: F401  (import for register() side effects)
    agent_instructions,
    content_patterns,
    github_actions,
    install_hooks,
    secrets_env,
)
from .detectors.base import run_detectors
from .engine import evaluate
from .filetree import FileTree
from .model import ReportModel
from .refine import downgrade_documentation_findings
from .rules import load_rules
from .score import SEVERITY_WEIGHT, blast_radius_rollup, score, verdict


def scan_tree(
    tree: FileTree, *, source: str, ref: str | None = None, scanned_at: str = ""
) -> ReportModel:
    facts = run_detectors(tree)
    rules = load_rules()
    findings = evaluate(rules, facts, tree)
    findings = downgrade_documentation_findings(findings)
    findings.sort(key=lambda f: (-SEVERITY_WEIGHT[f.severity], f.file, f.line))
    chains = build_chains(facts, tree)
    instr = [
        {"surface": f.data.get("surface"), "file": f.file, "content_excerpt": f.evidence}
        for f in facts
        if f.type == "agent.instruction_file"
    ]
    return ReportModel(
        repo={"source": source, "name": tree.root_name, "ref": ref, "scanned_at": scanned_at},
        verdict=verdict(findings),
        score=score(findings),
        findings=findings,
        blast_radius=blast_radius_rollup(findings),
        agent_instructions=instr,
        chains=chains,
        stats={
            "rules_run": len(rules),
            "files_scanned": len(tree.text_files()),
            "files_skipped": len(tree.entries) - len(tree.text_files()),
        },
    )


def scan(target: str, *, scanned_at: str = "") -> ReportModel:
    if os.path.exists(target):
        return scan_tree(load_local(target), source=f"local:{target}", scanned_at=scanned_at)
    owner, repo, ref = parse_github_url(target)  # raises ValueError if not a GitHub URL
    return scan_tree(load_remote(target), source=target, ref=ref, scanned_at=scanned_at)
