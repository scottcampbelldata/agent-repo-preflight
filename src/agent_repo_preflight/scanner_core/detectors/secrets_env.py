from __future__ import annotations

import re
from fnmatch import fnmatch

from ..facts import Fact
from ..filetree import FileTree
from .base import register

_BROAD = re.compile(
    r"(_TOKEN|_SECRET|_KEY|PASSWORD|AWS_|GITHUB_TOKEN|OPENAI_API_KEY|PRIVATE_KEY)", re.I
)


class SecretsEnvDetector:
    name = "secrets_env"

    def detect(self, tree: FileTree) -> list[Fact]:
        facts: list[Fact] = []
        for e in tree.entries:
            base = e.path.split("/")[-1]
            if not (
                fnmatch(base, ".env.example")
                or fnmatch(base, ".env.sample")
                or fnmatch(base, ".env.template")
            ):
                continue
            if not e.text:
                continue
            for i, line in enumerate(e.text.splitlines(), 1):
                key = line.split("=", 1)[0].strip()
                if key and _BROAD.search(key):
                    facts.append(
                        Fact(
                            "secret.broad_env_request",
                            e.path,
                            i,
                            {"key": key},
                            evidence=key,
                        )
                    )
        return facts


register(SecretsEnvDetector())
