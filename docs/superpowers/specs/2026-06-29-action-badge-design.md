# Agent Repo Preflight — Sub-project 3: GitHub Action + badge

**Status:** Approved design
**Date:** 2026-06-29
**Scope:** Third build cycle. A reusable GitHub Action that runs the scanner on PRs/pushes,
plus a status badge. Thin wrapper over the existing CLI — no new detection logic.

## Pitch

Maintainers add one workflow step and get an automatic "is this PR safe for AI agents?"
comment + check, and a README badge advertising "agent-preflight clean". Drives adoption
and spread (the badge is the viral surface).

## Decisions (committed)

- **Composite action** (`action.yml` at repo root), not Docker/JS. Reason: the tool is
  Python; a composite action reuses the runner's Python and is the lightest, fastest, most
  transparent option.
- **Self-contained install:** the action installs its own bundled copy with
  `pip install "$GITHUB_ACTION_PATH"`, so it works before the package is on PyPI and always
  matches the pinned action ref. (Once published, this could switch to `pip install
  agent-repo-preflight==<version>`.)
- **PR comment via `gh`** (preinstalled on runners), posting the CLI's `--markdown-report`
  output as a **sticky comment** (updated in place via an HTML marker, never spammed).
- **Least privilege:** the action needs `contents: read` + `pull-requests: write` (to
  comment). It never requests `write-all` — consistent with what the scanner itself flags.
- **`fail-on` input** controls the gate: `FAIL` (default — only a FAIL verdict fails the
  check), `REVIEW`, or `none` (always pass, comment only).

## Action interface (`action.yml`)

Inputs:
- `path` (default `.`) — directory to scan.
- `fail-on` (default `FAIL`) — `FAIL` | `REVIEW` | `none`.
- `comment` (default `true`) — post/update a PR comment (requires `pull-requests: write`).
- `github-token` (default `${{ github.token }}`) — for the comment + status.

Outputs:
- `verdict` — `PASS` | `REVIEW` | `FAIL`.
- `score` — numeric risk score.
- `report-json` — path to the written JSON report.

Behavior:
1. Set up Python, `pip install "$GITHUB_ACTION_PATH"`.
2. `agent-repo-preflight scan <path> --json > preflight-report.json` and
   `--markdown-report > preflight-report.md` (deterministic; the engine never runs target code).
3. If a PR context and `comment=true`: upsert a sticky comment with the markdown report.
4. Exit nonzero when the verdict meets/exceeds the `fail-on` threshold; else exit 0.

## Badge

Two paths, both documented in the README:

1. **Static badge** (zero infrastructure) — a shields.io static badge maintainers paste:
   `![Agent Preflight](https://img.shields.io/badge/agent--preflight-clean-brightgreen)`.
2. **Dynamic endpoint badge** — a new CLI option `scan ... --badge <file>` writes a
   shields.io *endpoint* JSON (`{"schemaVersion":1,"label":"agent-preflight","message":
   "<verdict>","color":"<color>"}`). Maintainers publish that JSON (e.g. as a CI artifact
   or committed file) and point a shields endpoint badge at its raw URL. Colors:
   PASS→brightgreen, REVIEW→yellow, FAIL→red.

## New / changed files

```
action.yml                                  # composite action
src/agent_repo_preflight/cli/main.py        # add scan --badge <file>
src/agent_repo_preflight/report_renderer/badge.py   # verdict -> shields endpoint dict
.github/workflows/preflight.yml             # dogfood: run our own action on this repo
README.md                                   # badge + Action usage
docs/github-action.md                       # full Action reference
tests/report_renderer/test_badge.py
tests/cli/test_cli_badge.py
```

## Testability

- `badge.py` is pure (`verdict -> dict`) — unit tested.
- `scan --badge <file>` writes the JSON — tested via the CLI in-process.
- `action.yml` is YAML (not unit-testable directly); validated by (a) running the CLI steps
  locally and (b) a dogfood workflow `.github/workflows/preflight.yml` that runs the action
  on this repo. The dogfood workflow uses `fail-on: none` because this repo intentionally
  ships malicious example fixtures.

## Out of scope (later)

- Marketplace publishing, auto-committing the badge JSON back to the repo, multi-repo
  org dashboards (the Postgres dashboard cycle), AI explanation summaries.
