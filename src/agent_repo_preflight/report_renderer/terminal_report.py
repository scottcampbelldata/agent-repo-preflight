from __future__ import annotations
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

_COLOR = {"PASS": "green", "REVIEW": "yellow", "FAIL": "red"}


def render_terminal(report, *, console: Console | None = None) -> None:
    console = console or Console()
    r = report
    color = _COLOR.get(r.verdict, "white")
    console.print(
        Panel(
            f"[bold {color}]AI-Agent Safety: {r.verdict}[/]\n"
            f"Repo: {r.repo['name']}  •  Risk score: {r.score}",
            title="Agent Repo Preflight",
            border_style=color,
        )
    )
    bt = Table(title="Blast radius")
    bt.add_column("Capability")
    bt.add_column("Level")
    for cap, level in r.blast_radius.items():
        bt.add_row(cap, level)
    console.print(bt)
    if r.findings:
        ft = Table(title="Findings")
        for col in ("Severity", "Rule", "Location", "Evidence"):
            ft.add_column(col, overflow="fold")
        for f in r.findings:
            ft.add_row(f.severity.upper(), f.rule_id, f"{f.file}:{f.line}", f.evidence[:60])
        console.print(ft)
    else:
        console.print("[green]No findings.[/]")
    if r.agent_instructions:
        console.print("[bold]Agent instruction surfaces:[/]")
        for ai in r.agent_instructions:
            console.print(f"  • {ai['surface']} ({ai['file']})")
    if r.chains:
        console.print("[bold]Suspicious setup chains (heuristic):[/]")
        for c in r.chains:
            console.print(
                "  " + " -> ".join(f"{s.kind}({s.file}:{s.line})" for s in c.steps)
            )
    console.print(f"[dim]{r.disclaimer}[/]")
