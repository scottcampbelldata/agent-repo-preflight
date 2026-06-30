from __future__ import annotations
from dataclasses import dataclass, asdict
from .findings import Finding
from .chains import Chain, ChainStep

DISCLAIMER = (
    "This tool detects repo-level risk indicators before AI agents execute "
    "setup, install, CI, MCP, or instruction files. It does not prove a "
    "repository is safe."
)


@dataclass
class ReportModel:
    repo: dict
    verdict: str
    score: int
    findings: list
    blast_radius: dict
    agent_instructions: list
    chains: list
    stats: dict
    schema_version: str = "1.0"
    disclaimer: str = DISCLAIMER

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "repo": self.repo,
            "verdict": self.verdict,
            "score": self.score,
            "findings": [asdict(f) for f in self.findings],
            "blast_radius": self.blast_radius,
            "agent_instructions": self.agent_instructions,
            "chains": [
                {"steps": [asdict(s) for s in c.steps]} for c in self.chains
            ],
            "stats": self.stats,
            "disclaimer": self.disclaimer,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ReportModel":
        findings = [Finding(**f) for f in d.get("findings", [])]
        chains = [
            Chain([ChainStep(**s) for s in c.get("steps", [])])
            for c in d.get("chains", [])
        ]
        return cls(
            repo=d.get("repo", {}),
            verdict=d.get("verdict", "PASS"),
            score=d.get("score", 0),
            findings=findings,
            blast_radius=d.get("blast_radius", {}),
            agent_instructions=d.get("agent_instructions", []),
            chains=chains,
            stats=d.get("stats", {}),
            schema_version=d.get("schema_version", "1.0"),
            disclaimer=d.get("disclaimer", DISCLAIMER),
        )
