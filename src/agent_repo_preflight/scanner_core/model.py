from __future__ import annotations
from dataclasses import dataclass, asdict

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
