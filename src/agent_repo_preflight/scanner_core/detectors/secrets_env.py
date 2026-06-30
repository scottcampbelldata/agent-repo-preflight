from __future__ import annotations

import re
from fnmatch import fnmatch

from ..facts import Fact
from ..filetree import FileTree
from .base import register

# Only genuinely high-blast-radius credentials: cloud root/secret keys, VCS/registry
# publish tokens, and private keys. Deliberately NOT bare *_API_KEY or *PASSWORD, which
# match ordinary app config (DB passwords, narrow third-party API keys) and cry wolf.
_BROAD = re.compile(
    r"AWS_SECRET_ACCESS_KEY|AWS_ACCESS_KEY_ID|AWS_SESSION_TOKEN"
    r"|AZURE_CLIENT_SECRET|GOOGLE_APPLICATION_CREDENTIALS|GCP_SA_KEY|GCP_SERVICE_ACCOUNT"
    r"|GITHUB_TOKEN|GH_TOKEN|GITLAB_TOKEN|NPM_TOKEN|PYPI_TOKEN|CARGO_TOKEN"
    r"|DIGITALOCEAN_TOKEN|HEROKU_API_KEY|CLOUDFLARE_API_TOKEN|SSH_PRIVATE_KEY"
    r"|PRIVATE_KEY|_SECRET_KEY$|CLIENT_SECRET",
    re.I,
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
