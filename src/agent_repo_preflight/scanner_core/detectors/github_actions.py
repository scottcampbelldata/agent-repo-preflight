from __future__ import annotations

import re

from ..facts import Fact
from ..filetree import FileTree
from .base import register
from .util import find_line

_SHA = re.compile(r"@[0-9a-f]{40}$")
_USES = re.compile(r"uses:\s*([^\s#]+)")


def _is_workflow(path: str) -> bool:
    return path.startswith(".github/workflows/") and (
        path.endswith(".yml") or path.endswith(".yaml")
    )


class GitHubActionsDetector:
    name = "github_actions"

    def detect(self, tree: FileTree) -> list[Fact]:
        facts: list[Fact] = []
        for e in tree.entries:
            if not _is_workflow(e.path) or not e.text:
                continue
            text = e.text
            if re.search(r"permissions:\s*write-all", text):
                facts.append(
                    Fact(
                        "ci.write_all_permissions",
                        e.path,
                        find_line(text, "write-all"),
                        {},
                        evidence="permissions: write-all",
                    )
                )
            prt = "pull_request_target" in text
            if prt:
                facts.append(
                    Fact(
                        "ci.pull_request_target",
                        e.path,
                        find_line(text, "pull_request_target"),
                        {},
                        evidence="on: pull_request_target",
                    )
                )
            for i, line in enumerate(text.splitlines(), 1):
                m = _USES.search(line)
                if m:
                    ref = m.group(1)
                    if "@" in ref and not _SHA.search(ref):
                        facts.append(
                            Fact(
                                "ci.unpinned_action",
                                e.path,
                                i,
                                {"action": ref},
                                evidence=ref,
                            )
                        )
            if (
                prt
                and ("github.event.pull_request.head" in text or "head.ref" in text)
                and "run:" in text
            ):
                facts.append(
                    Fact(
                        "ci.untrusted_checkout_exec",
                        e.path,
                        1,
                        {},
                        evidence="pull_request_target + PR head checkout + run",
                    )
                )
        return facts


register(GitHubActionsDetector())
