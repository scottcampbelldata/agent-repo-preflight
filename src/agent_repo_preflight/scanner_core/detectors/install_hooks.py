from __future__ import annotations
import json
import re
import tomllib
from ..facts import Fact
from ..filetree import FileTree
from .base import register
from .util import find_line

LIFECYCLE = {
    "preinstall",
    "install",
    "postinstall",
    "prepare",
    "prepublish",
    "prepublishOnly",
}
_NET_EXEC = re.compile(
    r"os\.system|subprocess|urllib|requests\.|socket\.|curl|wget|exec\(|eval\("
)
_KNOWN_BACKENDS = (
    "hatchling.build",
    "setuptools.build_meta",
    "flit_core.buildapi",
    "poetry.core.masonry.api",
    "pdm.backend",
    "maturin",
)


class PackageJsonDetector:
    name = "package_json"

    def detect(self, tree: FileTree) -> list[Fact]:
        facts: list[Fact] = []
        for e in tree.match("package.json"):
            if not e.text:
                continue
            try:
                data = json.loads(e.text)
            except ValueError:
                continue
            scripts = data.get("scripts", {}) if isinstance(data, dict) else {}
            for hook, cmd in scripts.items():
                if hook in LIFECYCLE and isinstance(cmd, str):
                    facts.append(
                        Fact(
                            "pkg.lifecycle_script",
                            e.path,
                            find_line(e.text, cmd),
                            {"hook": hook, "command": cmd},
                            evidence=cmd,
                        )
                    )
        return facts


class PythonInstallDetector:
    name = "python_install"

    def detect(self, tree: FileTree) -> list[Fact]:
        facts: list[Fact] = []
        for e in tree.match("setup.py"):
            if not e.text:
                continue
            for i, line in enumerate(e.text.splitlines(), 1):
                if _NET_EXEC.search(line):
                    facts.append(
                        Fact("py.setup_network", e.path, i, {}, evidence=line.strip())
                    )
        for e in tree.match("pyproject.toml"):
            if not e.text:
                continue
            try:
                doc = tomllib.loads(e.text)
            except (tomllib.TOMLDecodeError, ValueError):
                continue
            backend = doc.get("build-system", {}).get("build-backend")
            if backend and backend not in _KNOWN_BACKENDS:
                facts.append(
                    Fact(
                        "py.pyproject_build_hook",
                        e.path,
                        find_line(e.text, "build-backend"),
                        {"backend": backend},
                        evidence=f"build-backend = {backend}",
                    )
                )
        return facts


register(PackageJsonDetector())
register(PythonInstallDetector())
