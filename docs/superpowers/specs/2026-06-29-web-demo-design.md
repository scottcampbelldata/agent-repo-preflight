# Agent Repo Preflight — Sub-project 2: Web demo

**Status:** Approved design
**Date:** 2026-06-29
**Scope:** Second build cycle. A shareable, visual web front-end over the existing scan engine.

## Pitch

Paste a public GitHub URL, get a shareable "safe for AI agent use?" report page. The
attention engine for the project: visual, instantly understandable, link-shareable.

This cycle is a **front-end over `scanner_core`** — it adds no detection logic. The engine
(`ReportModel`, JSON `schema_version: "1.0"`) is reused in-process, unchanged.

## Architecture

A single FastAPI application (`agent_repo_preflight.web`) that imports `scanner_core`
directly (no network hop, no second language/runtime). Server-rendered HTML via Jinja2 +
one CSS file. Packaged behind a `[web]` optional-dependency extra so the core CLI stays
lightweight.

```
browser → FastAPI route → scanner_core.scan() (in-process)
        → ScanStore.save(report.to_dict()) → redirect /report/{id}
/report/{id} → ScanStore.get(id) → Jinja template → HTML
```

## Routes

| Method | Path | Purpose |
|---|---|---|
| GET | `/` | Scan form (paste GitHub URL) + recent scans list |
| POST | `/scan` | Validate URL, run scan, persist, redirect to permalink |
| GET | `/report/{id}` | Visual HTML report (trust card, blast radius, findings, chains, agent instructions) |
| GET | `/report/{id}.json` | Same report as JSON (reuses `render_json` over stored dict) |
| GET | `/report/{id}.md` | Same report as Markdown (reuses `render_markdown`) |
| GET | `/examples` | Two pre-seeded reports (clean + high-risk), scanned from bundled `examples/` at startup |
| GET | `/rules` | The loaded ruleset |

## Persistence

`ScanStore` protocol with a `SqliteScanStore` implementation. Single table:

```
scans(id TEXT PK, source TEXT, name TEXT, verdict TEXT, score INT,
      scanned_at TEXT, report_json TEXT, created_at TEXT)
```

The full `ReportModel.to_dict()` is stored as JSON in `report_json`; report pages
re-render from storage with no re-scan. `ScanStore` interface:

- `save(report_dict: dict, *, created_at: str) -> str` (returns new id)
- `get(id: str) -> dict | None` (returns the stored report dict)
- `list_recent(limit: int = 20) -> list[dict]` (id, source, name, verdict, score, created_at)

Swapping to Postgres later = a new adapter implementing the same protocol; no route changes.
Ids are random hex (`secrets.token_hex(8)`) — generated at the web boundary, not in the
deterministic engine.

## Security / abuse posture

- **SSRF-safe by construction:** only `github.com` URLs are accepted. `parse_github_url`
  rejects everything else; the only outbound fetch target is `codeload.github.com`.
- Engine size/file caps (50 MB tarball, per-file/byte caps) already bound resource use.
- Scan runs **synchronously** within the request. Acceptable for a demo; a job queue is
  deferred to the dashboard cycle. A friendly error page is shown on fetch/scan failure.
- The web app **still never executes target repo code** — same guarantee as the CLI.

## Testability

- Routes delegate the actual scan to an **injectable callable** (FastAPI dependency /
  app state), so `TestClient` tests fake the scanner and never hit live GitHub.
- `SqliteScanStore` is tested directly against a temp-file DB (save/get/list roundtrip).
- Report rendering is tested by pre-seeding the store with a known report dict and
  asserting the HTML contains the verdict, findings, blast radius, and disclaimer.

## Visual design

- **Trust card**: large, color-coded (green PASS / amber REVIEW / red FAIL) with the
  one-line verdict and repo name.
- **Blast-radius grid**: six capability chips, colored by level (HIGH/MED/LOW/NONE).
- **Findings**: grouped by severity (critical→info), each a card with rule, file:line,
  evidence, explanation, remediation.
- **Setup-chain**: the heuristic chain rendered as a stepped flow (the screenshot moment).
- **Agent instructions**: a dedicated section listing every instruction surface found.
- Disclaimer in the footer of every report. Honest copy: never claims "safe".

## Run

```
python -m agent_repo_preflight.web        # serves via uvicorn on 127.0.0.1:8000
```

## Out of scope (later cycles)

- Job queue / async scanning, Postgres, the aggregate dashboard (top risky patterns,
  trends), GitHub Action, badge, AI explanation summaries. All designed-for; none built here.

## Files (new)

```
src/agent_repo_preflight/web/
  __init__.py
  __main__.py            # uvicorn launcher
  app.py                 # FastAPI app + routes
  store.py               # ScanStore protocol + SqliteScanStore
  templates/             # base, index, report, examples, rules, error
  static/style.css
tests/web/
  test_store.py
  test_routes.py
```
