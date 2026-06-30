from __future__ import annotations

import re
from fnmatch import fnmatch

from ..facts import Fact
from ..filetree import FileTree
from .base import register

_SURFACES = [
    ("CLAUDE.md", "CLAUDE.md"),
    (".cursor/rules*", "cursor-rules"),
    (".cursorrules", "cursor-rules"),
    (".windsurfrules", "windsurf"),
    (".windsurf*", "windsurf"),
    (".github/copilot-instructions.md", "copilot-instructions"),
]
_MCP_NAMES = ("*.mcp.json", "mcp.json", ".mcp.json", "*mcp*.json")
_POWER_TOOLS = ("shell", "filesystem", "exec", "terminal", "bash", "subprocess")
_UNVERIFIED = re.compile(r"run\b.{0,40}\bwithout\b.{0,30}(review|inspect|check|read)", re.I)


def _surface_for(path: str) -> str | None:
    base = path.split("/")[-1]
    for pat, surface in _SURFACES:
        if fnmatch(path, pat) or fnmatch(base, pat):
            return surface
    if any(fnmatch(base, n) for n in _MCP_NAMES):
        return "mcp-config"
    return None


class AgentInstructionDetector:
    name = "agent_instructions"

    def detect(self, tree: FileTree) -> list[Fact]:
        facts: list[Fact] = []
        for e in tree.entries:
            surface = _surface_for(e.path)
            if not surface:
                continue
            facts.append(
                Fact(
                    "agent.instruction_file",
                    e.path,
                    1,
                    {"surface": surface},
                    evidence=(e.text or "")[:300],
                )
            )
            if not e.text:
                continue
            for i, line in enumerate(e.text.splitlines(), 1):
                if _UNVERIFIED.search(line):
                    facts.append(
                        Fact(
                            "agent.instruction_run_unverified",
                            e.path,
                            i,
                            {},
                            evidence=line.strip(),
                        )
                    )
            if surface == "mcp-config":
                low = e.text.lower()
                for tool in _POWER_TOOLS:
                    if tool in low:
                        facts.append(
                            Fact(
                                "agent.mcp_tool_grant",
                                e.path,
                                1,
                                {"tool": tool},
                                evidence=tool,
                            )
                        )
        return facts


register(AgentInstructionDetector())
