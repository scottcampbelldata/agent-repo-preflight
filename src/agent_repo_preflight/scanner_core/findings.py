from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class Finding:
    rule_id: str
    severity: str
    category: str
    file: str
    line: int
    evidence: str
    explanation: str
    remediation: str
    blast_radius: list[str] = field(default_factory=list)
