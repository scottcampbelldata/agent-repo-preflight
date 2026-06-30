from __future__ import annotations
import argparse
import sys
from datetime import datetime, timezone
from ..scanner_core.scan import scan
from ..scanner_core.rules import load_rules
from ..report_renderer.json_report import render_json
from ..report_renderer.markdown_report import render_markdown
from ..report_renderer.terminal_report import render_terminal

_EXIT = {"PASS": 0, "REVIEW": 1, "FAIL": 2}


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="agent-repo-preflight",
        description="Preflight safety scanner for repos before AI coding agents run them.",
    )
    sub = p.add_subparsers(dest="command", required=True)
    s = sub.add_parser("scan", help="Scan a local folder or GitHub URL")
    s.add_argument("target")
    s.add_argument("--json", action="store_true")
    s.add_argument("--markdown-report", action="store_true")
    sub.add_parser("rules", help="List loaded rules")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "rules":
        for r in load_rules():
            print(f"{r.severity:8} {r.id:34} {r.name}")
        return 0
    try:
        report = scan(args.target, scanned_at=datetime.now(timezone.utc).isoformat())
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 3
    except Exception as exc:  # network/IO failures
        print(f"error: scan failed: {exc}", file=sys.stderr)
        return 3
    if args.json:
        print(render_json(report))
    elif args.markdown_report:
        print(render_markdown(report))
    else:
        render_terminal(report)
    return _EXIT.get(report.verdict, 3)


if __name__ == "__main__":
    raise SystemExit(main())
