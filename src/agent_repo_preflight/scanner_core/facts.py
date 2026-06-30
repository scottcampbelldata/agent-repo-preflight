from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class Fact:
    type: str
    file: str
    line: int
    data: dict = field(default_factory=dict)
    evidence: str = ""
