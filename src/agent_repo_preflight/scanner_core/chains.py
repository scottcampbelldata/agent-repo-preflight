from __future__ import annotations

import re
from dataclasses import dataclass, field

from .facts import Fact
from .filetree import FileTree


@dataclass
class ChainStep:
    kind: str
    file: str
    line: int
    detail: str


@dataclass
class Chain:
    steps: list[ChainStep] = field(default_factory=list)


_SCRIPT_REF = re.compile(r"([\w./-]+\.(?:js|cjs|mjs|sh|py|ts))")


def _readme_mentions_install(tree: FileTree) -> ChainStep | None:
    for e in tree.match("README*"):
        if e.text and re.search(r"npm install|yarn|pnpm install|pip install|setup", e.text, re.I):
            return ChainStep(
                "readme_instruction", e.path, 1, "README instructs running install/setup"
            )
    return None


def build_chains(facts: list[Fact], tree: FileTree) -> list[Chain]:
    chains: list[Chain] = []
    content_by_file: dict[str, list[Fact]] = {}
    for f in facts:
        if f.type.startswith("content."):
            content_by_file.setdefault(f.file, []).append(f)
    readme = _readme_mentions_install(tree)
    for f in facts:
        if f.type != "pkg.lifecycle_script":
            continue
        steps: list[ChainStep] = []
        if readme:
            steps.append(readme)
        steps.append(
            ChainStep(
                "lifecycle_hook",
                f.file,
                f.line,
                f"{f.data.get('hook')}: {f.data.get('command')}",
            )
        )
        m = _SCRIPT_REF.search(f.data.get("command", ""))
        if m:
            ref = m.group(1).lstrip("./")
            target = next((e for e in tree.entries if e.path.endswith(ref)), None)
            if target:
                steps.append(ChainStep("referenced_script", target.path, 1, f"runs {target.path}"))
                for cf in content_by_file.get(target.path, []):
                    steps.append(ChainStep("dangerous_call", cf.file, cf.line, cf.evidence))
        if len(steps) >= 2:
            chains.append(Chain(steps))
    return chains
