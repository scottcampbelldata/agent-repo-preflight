from __future__ import annotations

import os
from datetime import UTC, datetime

from fastapi import FastAPI, Form, Request
from fastapi.responses import (
    HTMLResponse,
    JSONResponse,
    PlainTextResponse,
    RedirectResponse,
)
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from ..report_renderer.markdown_report import render_markdown
from ..scanner_core.acquire_local import load_local
from ..scanner_core.acquire_remote import load_remote, parse_github_url
from ..scanner_core.model import ReportModel
from ..scanner_core.rules import load_rules
from ..scanner_core.scan import scan_tree
from .store import ScanStore, SqliteScanStore

_HERE = os.path.dirname(__file__)
_TEMPLATES = os.path.join(_HERE, "templates")
_STATIC = os.path.join(_HERE, "static")


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _remote_scan(target: str, *, scanned_at: str = "") -> ReportModel:
    # Web boundary is remote-only: never scan a local server path (LFI guard).
    owner, repo, ref = parse_github_url(target)  # raises ValueError on non-GitHub
    return scan_tree(load_remote(target), source=target, ref=ref, scanned_at=scanned_at)


def _find_examples_dir() -> str | None:
    # Explicit override (used by the Docker image, where examples are bundled at a
    # known path rather than sitting above the installed package).
    env_dir = os.environ.get("AGENT_PREFLIGHT_EXAMPLES_DIR")
    if env_dir and os.path.isdir(env_dir):
        return env_dir
    # Otherwise walk up from the package looking for a top-level `examples/` directory.
    d = _HERE
    for _ in range(6):
        d = os.path.dirname(d)
        cand = os.path.join(d, "examples")
        if os.path.isdir(cand):
            return cand
    return None


def _seed_examples(store: ScanStore) -> list[dict]:
    ex_dir = _find_examples_dir()
    seeded: list[dict] = []
    if not ex_dir:
        return seeded
    for name in ("clean", "suspicious-node"):
        path = os.path.join(ex_dir, name)
        if not os.path.isdir(path):
            continue
        report = scan_tree(load_local(path), source=f"example:{name}", scanned_at=_now())
        sid = store.save(report.to_dict(), created_at=_now())
        seeded.append({"id": sid, "name": name, "verdict": report.verdict, "score": report.score})
    return seeded


def create_app(store: ScanStore | None = None, scanner=None) -> FastAPI:
    if store is None:
        store = SqliteScanStore(os.environ.get("AGENT_PREFLIGHT_DB", "preflight.db"))
    if scanner is None:
        scanner = _remote_scan

    app = FastAPI(title="Agent Repo Preflight")
    app.mount("/static", StaticFiles(directory=_STATIC), name="static")
    templates = Jinja2Templates(directory=_TEMPLATES)

    examples = _seed_examples(store)

    @app.get("/", response_class=HTMLResponse)
    def home(request: Request):
        return templates.TemplateResponse(request, "index.html", {"recent": store.list_recent(10)})

    @app.post("/scan")
    def run_scan(request: Request, target: str = Form(...)):
        target = target.strip()
        try:
            parse_github_url(target)  # boundary guard: GitHub-only, no local paths
        except ValueError as exc:
            return templates.TemplateResponse(
                request,
                "error.html",
                {"message": f"{exc} Only public github.com URLs are supported."},
                status_code=400,
            )
        try:
            report = scanner(target, scanned_at=_now())
        except ValueError as exc:
            return templates.TemplateResponse(
                request,
                "error.html",
                {"message": f"{exc} Only public github.com URLs are supported."},
                status_code=400,
            )
        except Exception as exc:  # network / IO failure
            return templates.TemplateResponse(
                request,
                "error.html",
                {"message": f"Scan failed: {exc}"},
                status_code=502,
            )
        sid = store.save(report.to_dict(), created_at=_now())
        return RedirectResponse(f"/report/{sid}", status_code=303)

    @app.get("/report/{id}.json")
    def report_json(id: str):
        data = store.get(id)
        if data is None:
            return JSONResponse({"error": "not found"}, status_code=404)
        return JSONResponse(data)

    @app.get("/report/{id}.md", response_class=PlainTextResponse)
    def report_md(id: str):
        data = store.get(id)
        if data is None:
            return PlainTextResponse("not found", status_code=404)
        return PlainTextResponse(render_markdown(ReportModel.from_dict(data)))

    @app.get("/report/{id}", response_class=HTMLResponse)
    def report_html(request: Request, id: str):
        data = store.get(id)
        if data is None:
            return templates.TemplateResponse(
                request,
                "error.html",
                {"message": "No report with that id."},
                status_code=404,
            )
        return templates.TemplateResponse(request, "report.html", {"report": data, "id": id})

    @app.get("/examples", response_class=HTMLResponse)
    def examples_page(request: Request):
        return templates.TemplateResponse(request, "examples.html", {"examples": examples})

    @app.get("/rules", response_class=HTMLResponse)
    def rules_page(request: Request):
        return templates.TemplateResponse(request, "rules.html", {"rules": load_rules()})

    return app
