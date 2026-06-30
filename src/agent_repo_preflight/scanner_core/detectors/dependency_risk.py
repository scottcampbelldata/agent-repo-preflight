from __future__ import annotations

import json
import re
from fnmatch import fnmatch

from ..facts import Fact
from ..filetree import FileTree
from .base import register
from .util import find_line

# Native executables / loadable modules / installers that an agent could run if checked
# into a repo. Deliberately excludes common benign build artifacts (.jar, .class, .pyc).
_BINARY_EXT = (
    ".exe",
    ".dll",
    ".so",
    ".dylib",
    ".node",
    ".wasm",
    ".msi",
    ".deb",
    ".rpm",
    ".dmg",
    ".pkg",
    ".app",
    ".bin",
    ".out",
    ".com",
    ".scr",
)

# A dependency spec that installs from an arbitrary URL/VCS bypasses registry vetting.
_URL_SPEC = re.compile(r"(git\+|https?://|git://|ssh://|github:|file:)", re.I)
_REQ_URL = re.compile(r"^\s*(-e\s+)?(git\+|https?://|git://|ssh://)", re.I)


class BinaryArtifactDetector:
    name = "binary_artifacts"

    def detect(self, tree: FileTree) -> list[Fact]:
        facts: list[Fact] = []
        for e in tree.entries:
            low = e.path.lower()
            for ext in _BINARY_EXT:
                if low.endswith(ext):
                    facts.append(
                        Fact(
                            "artifact.checked_in_binary",
                            e.path,
                            1,
                            {"ext": ext},
                            evidence=e.path,
                        )
                    )
                    break
        return facts


class DependencyRiskDetector:
    name = "dependency_risk"

    def detect(self, tree: FileTree) -> list[Fact]:
        facts: list[Fact] = []
        for e in tree.text_files():
            base = e.path.split("/")[-1]
            if base == "package.json":
                facts.extend(self._package_json(e))
            elif base in ("requirements.txt",) or fnmatch(base, "requirements*.txt"):
                facts.extend(self._requirements(e))
            elif base == ".npmrc":
                facts.extend(self._npmrc(e))
        return facts

    def _package_json(self, e) -> list[Fact]:
        try:
            doc = json.loads(e.text)
        except ValueError:
            return []
        out: list[Fact] = []
        for section in ("dependencies", "devDependencies", "optionalDependencies"):
            deps = doc.get(section, {}) if isinstance(doc, dict) else {}
            if not isinstance(deps, dict):
                continue
            for name, spec in deps.items():
                if isinstance(spec, str) and _URL_SPEC.search(spec):
                    out.append(
                        Fact(
                            "dep.url_install",
                            e.path,
                            find_line(e.text, name),
                            {"name": name, "spec": spec, "manifest": "package.json"},
                            evidence=f"{name}: {spec}"[:200],
                        )
                    )
        return out

    def _requirements(self, e) -> list[Fact]:
        out: list[Fact] = []
        for i, line in enumerate(e.text.splitlines(), 1):
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            if _REQ_URL.search(s) or s.lower().endswith((".whl", ".tar.gz")):
                out.append(
                    Fact(
                        "dep.url_install",
                        e.path,
                        i,
                        {"name": s.split("#")[0][:60], "spec": s, "manifest": "requirements.txt"},
                        evidence=s[:200],
                    )
                )
            elif s.startswith(("--index-url", "--extra-index-url")):
                out.append(
                    Fact(
                        "dep.custom_registry",
                        e.path,
                        i,
                        {"file": e.path},
                        evidence=s[:200],
                    )
                )
        return out

    def _npmrc(self, e) -> list[Fact]:
        out: list[Fact] = []
        for i, line in enumerate(e.text.splitlines(), 1):
            s = line.strip()
            if s.startswith("registry=") and "registry.npmjs.org" not in s:
                out.append(
                    Fact("dep.custom_registry", e.path, i, {"file": e.path}, evidence=s[:200])
                )
            elif "_authToken" in s:
                out.append(
                    Fact(
                        "dep.custom_registry",
                        e.path,
                        i,
                        {"file": e.path, "token": True},
                        evidence="npmrc contains an auth token",
                    )
                )
        return out


register(BinaryArtifactDetector())
register(DependencyRiskDetector())
