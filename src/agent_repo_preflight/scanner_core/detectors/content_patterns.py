from __future__ import annotations
import re
from fnmatch import fnmatch
from ..facts import Fact
from ..filetree import FileTree
from .base import register

PATTERNS: dict[str, re.Pattern] = {
    "curl_pipe_sh": re.compile(r"curl\b[^\n|]*\|\s*(ba)?sh", re.I),
    "wget_pipe_sh": re.compile(r"wget\b[^\n|]*\|\s*(ba)?sh", re.I),
    "invoke_webrequest": re.compile(r"Invoke-WebRequest|Invoke-RestMethod", re.I),
    "start_process": re.compile(r"Start-Process", re.I),
    "netcat": re.compile(r"\bnc\b\s+-[a-z]*e|\bncat\b", re.I),
    "socat": re.compile(r"\bsocat\b", re.I),
    "chmod_x": re.compile(r"chmod\s+\+x|chmod\s+[0-7]*7[0-7]*"),
    "encoded_powershell": re.compile(r"-enc(odedcommand)?\b|FromBase64String", re.I),
    "base64_exec": re.compile(
        r"base64\s+-d[^\n|]*\|\s*(ba)?sh|base64\s+--decode[^\n|]*\|\s*(ba)?sh"
        r"|atob\(|FromBase64String",
        re.I,
    ),
    "dns_txt": re.compile(
        r"dig\s+[^\n]*\btxt\b|nslookup\s+-type=txt|resolver?\.query\([^)]*TXT", re.I
    ),
    "dev_tcp": re.compile(r"/dev/tcp/"),
    "cred_path_read": re.compile(
        r"~/\.ssh|~/\.aws|\.aws/credentials|\.npmrc|\.pypirc|/etc/shadow"
        r"|\.docker/config\.json|\.kube/config|id_rsa|Login Data",
        re.I,
    ),
}


class ContentPatternDetector:
    name = "content_patterns"

    def detect(self, tree: FileTree) -> list[Fact]:
        facts: list[Fact] = []
        for e in tree.text_files():
            for i, line in enumerate(e.text.splitlines(), 1):
                for pid, rx in PATTERNS.items():
                    if rx.search(line):
                        facts.append(
                            Fact(
                                f"content.{pid}",
                                e.path,
                                i,
                                {"pattern_id": pid},
                                evidence=line.strip()[:200],
                            )
                        )
        return facts


_SHELL_KINDS = [
    ("install.sh", "install.sh"),
    ("*.ps1", "powershell"),
    ("*.bat", "batch"),
    ("Makefile", "makefile"),
]


class ShellScriptDetector:
    name = "shell_scripts"

    def detect(self, tree: FileTree) -> list[Fact]:
        facts: list[Fact] = []
        for e in tree.entries:
            base = e.path.split("/")[-1]
            for glob, kind in _SHELL_KINDS:
                if fnmatch(base, glob):
                    facts.append(
                        Fact(
                            "shell.script_present",
                            e.path,
                            1,
                            {"kind": glob if kind == "install.sh" else kind},
                        )
                    )
        return facts


register(ContentPatternDetector())
register(ShellScriptDetector())
