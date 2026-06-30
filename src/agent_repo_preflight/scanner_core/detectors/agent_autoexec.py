from __future__ import annotations

from fnmatch import fnmatch

from ..facts import Fact
from ..filetree import FileTree
from .base import register
from .util import find_line, load_jsonc

# devcontainer lifecycle commands run automatically when an agent opens the repo in a
# Codespace / Dev Container. https://containers.dev/implementors/json_reference/
_DEVCONTAINER_HOOKS = (
    "initializeCommand",
    "onCreateCommand",
    "updateContentCommand",
    "postCreateCommand",
    "postStartCommand",
    "postAttachCommand",
)


def _command_to_str(value) -> str | None:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return " ".join(str(v) for v in value)
    if isinstance(value, dict):  # object form: {"label": "cmd", ...}
        return " ".join(str(v) for v in value.values())
    return None


def _is_devcontainer(path: str) -> bool:
    base = path.split("/")[-1]
    return base == "devcontainer.json" and (".devcontainer" in path or path == "devcontainer.json")


class DevcontainerDetector:
    name = "devcontainer"

    def detect(self, tree: FileTree) -> list[Fact]:
        facts: list[Fact] = []
        for e in tree.entries:
            if not _is_devcontainer(e.path) or not e.text:
                continue
            doc = load_jsonc(e.text)
            if not isinstance(doc, dict):
                continue
            for hook in _DEVCONTAINER_HOOKS:
                if hook in doc:
                    cmd = _command_to_str(doc[hook])
                    if cmd:
                        facts.append(
                            Fact(
                                "agent.devcontainer_hook",
                                e.path,
                                find_line(e.text, hook),
                                {"hook": hook, "command": cmd},
                                evidence=f"{hook}: {cmd}"[:200],
                            )
                        )
        return facts


class VSCodeTasksDetector:
    name = "vscode_tasks"

    def detect(self, tree: FileTree) -> list[Fact]:
        facts: list[Fact] = []
        for e in tree.entries:
            if not (fnmatch(e.path, "*.vscode/tasks.json") or e.path == ".vscode/tasks.json"):
                continue
            if not e.text:
                continue
            doc = load_jsonc(e.text)
            if not isinstance(doc, dict):
                continue
            for task in doc.get("tasks", []) or []:
                if not isinstance(task, dict):
                    continue
                run_on = (task.get("runOptions") or {}).get("runOn")
                if run_on == "folderOpen":
                    cmd = _command_to_str(task.get("command")) or task.get("label", "")
                    facts.append(
                        Fact(
                            "editor.vscode_autotask",
                            e.path,
                            find_line(e.text, "folderOpen"),
                            {"command": cmd},
                            evidence=f"runOn=folderOpen: {cmd}"[:200],
                        )
                    )
        return facts


class EnvrcDetector:
    name = "direnv"

    def detect(self, tree: FileTree) -> list[Fact]:
        facts: list[Fact] = []
        for e in tree.entries:
            if e.path == ".envrc" or e.path.endswith("/.envrc"):
                first = (e.text or "").strip().splitlines()
                facts.append(
                    Fact(
                        "editor.direnv_envrc",
                        e.path,
                        1,
                        {},
                        evidence=(first[0] if first else "")[:200],
                    )
                )
        return facts


register(DevcontainerDetector())
register(VSCodeTasksDetector())
register(EnvrcDetector())
