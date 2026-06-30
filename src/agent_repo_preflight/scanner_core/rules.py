from __future__ import annotations

import glob
import os
from dataclasses import dataclass, field

import yaml

SEVERITIES = ["info", "low", "medium", "high", "critical"]
BLAST_CAPS = ["filesystem", "network", "secrets", "shell", "install_hooks", "ci"]


class RuleError(ValueError):
    pass


@dataclass
class Rule:
    id: str
    name: str
    severity: str
    category: str
    explanation: str
    remediation: str
    blast_radius: list[str] = field(default_factory=list)
    match: dict = field(default_factory=dict)
    references: list[str] = field(default_factory=list)


def _packaged_dir() -> str:
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), "rules_data")


def _validate(doc: dict, path: str) -> Rule:
    required = ["id", "name", "severity", "category", "explanation", "remediation"]
    for key in required:
        if key not in doc:
            raise RuleError(f"{path}: missing required field '{key}'")
    if doc["severity"] not in SEVERITIES:
        raise RuleError(f"{path}: invalid severity '{doc['severity']}'")
    for cap in doc.get("blast_radius", []) or []:
        if cap not in BLAST_CAPS:
            raise RuleError(f"{path}: invalid blast_radius '{cap}'")
    return Rule(
        id=doc["id"],
        name=doc["name"],
        severity=doc["severity"],
        category=doc["category"],
        explanation=doc["explanation"],
        remediation=doc["remediation"],
        blast_radius=list(doc.get("blast_radius", []) or []),
        match=doc.get("match", {}) or {},
        references=list(doc.get("references", []) or []),
    )


def load_rules(directory: str | None = None) -> list[Rule]:
    directory = directory or _packaged_dir()
    rules: list[Rule] = []
    for fp in sorted(glob.glob(os.path.join(directory, "*.yaml"))):
        with open(fp, encoding="utf-8") as fh:
            doc = yaml.safe_load(fh)
        if not isinstance(doc, dict):
            raise RuleError(f"{fp}: rule file must be a mapping")
        rules.append(_validate(doc, fp))
    return rules
