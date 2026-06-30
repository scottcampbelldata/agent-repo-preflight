from __future__ import annotations

import json
import re

_TRAILING_COMMA = re.compile(r",(\s*[}\]])")


def find_line(text: str, needle: str) -> int:
    for i, line in enumerate(text.splitlines(), start=1):
        if needle in line:
            return i
    return 1


def _strip_jsonc_comments(text: str) -> str:
    """Remove // and /* */ comments without touching // inside string literals."""
    out: list[str] = []
    i, n = 0, len(text)
    in_str = False
    while i < n:
        c = text[i]
        if in_str:
            out.append(c)
            if c == "\\" and i + 1 < n:  # keep escaped char verbatim
                out.append(text[i + 1])
                i += 2
                continue
            if c == '"':
                in_str = False
            i += 1
            continue
        if c == '"':
            in_str = True
            out.append(c)
            i += 1
        elif c == "/" and i + 1 < n and text[i + 1] == "/":
            while i < n and text[i] != "\n":
                i += 1
        elif c == "/" and i + 1 < n and text[i + 1] == "*":
            i += 2
            while i + 1 < n and not (text[i] == "*" and text[i + 1] == "/"):
                i += 1
            i += 2
        else:
            out.append(c)
            i += 1
    return "".join(out)


def load_jsonc(text: str):
    """Parse JSON-with-comments (devcontainer.json, VS Code config) tolerantly.

    Strips // and /* */ comments (outside strings) and trailing commas before
    json.loads. Returns the parsed value, or None if it still cannot be parsed.
    """
    cleaned = _strip_jsonc_comments(text)
    cleaned = _TRAILING_COMMA.sub(r"\1", cleaned)
    try:
        return json.loads(cleaned)
    except ValueError:
        return None
