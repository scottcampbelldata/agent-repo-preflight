from __future__ import annotations

import re
from fnmatch import fnmatch

from .facts import Fact
from .filetree import FileTree
from .findings import Finding
from .rules import Rule


def _patterns_match(patterns: list[str], haystacks: list[str]) -> bool:
    if not patterns:
        return True
    for p in patterns:
        rx = re.compile(p, re.I)
        if any(rx.search(h) for h in haystacks if h):
            return True
    return False


def _finding(rule: Rule, file: str, line: int, evidence: str) -> Finding:
    return Finding(
        rule.id,
        rule.severity,
        rule.category,
        file,
        line,
        evidence,
        rule.explanation,
        rule.remediation,
        list(rule.blast_radius),
    )


def evaluate(rules: list[Rule], facts: list[Fact], tree: FileTree) -> list[Finding]:
    seen: set[tuple] = set()
    out: list[Finding] = []

    def emit(f: Finding):
        key = (f.rule_id, f.file, f.line)
        if key not in seen:
            seen.add(key)
            out.append(f)

    for rule in rules:
        m = rule.match or {}
        fact_types = m.get("facts") or []
        patterns = m.get("patterns") or []
        file_patterns = m.get("file_patterns") or []
        if fact_types:
            for fact in facts:
                if fact.type not in fact_types:
                    continue
                hay = [fact.evidence] + [str(v) for v in fact.data.values()]
                if _patterns_match(patterns, hay):
                    evidence = fact.evidence or (hay[0] if hay else "")
                    emit(_finding(rule, fact.file, fact.line, evidence))
        elif patterns:
            for e in tree.text_files():
                if file_patterns and not any(
                    fnmatch(e.path, g) or fnmatch(e.path.split("/")[-1], g) for g in file_patterns
                ):
                    continue
                for i, line in enumerate(e.text.splitlines(), 1):
                    if _patterns_match(patterns, [line]):
                        emit(_finding(rule, e.path, i, line.strip()[:200]))
    return out
