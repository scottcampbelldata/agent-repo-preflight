# Agent Repo Preflight — Sub-project 1: scanner-core + CLI

**Status:** Approved design
**Date:** 2026-06-29
**Scope:** First build cycle of `agent-repo-preflight`. Foundational scan engine + CLI only.

## Project pitch

A local-first scanner that audits a GitHub repository (or local folder) for hidden
risks **before** an AI coding agent (Claude Code, Codex, Cursor, Copilot Agent,
Windsurf, Aider, etc.) clones, installs, modifies, or executes it.

Hook: `uvx agent-repo-preflight scan https://github.com/org/repo` → a
"safe for AI agent use?" report with a verdict, evidence, and remediation.

Honesty constraint (a core trust claim): **the scanner never executes target
repository code**, and it never claims a repo is "safe" — only that it did or did
not find risk indicators.

## In scope (this cycle)

- Acquisition: local path **or** GitHub URL via codeload **tarball download** (no git, no execution).
- Detectors emitting structured Facts.
- YAML rule engine matching Facts + raw content patterns → Findings.
- Scoring + verdict (PASS / REVIEW / FAIL) and per-capability blast-radius rollup.
- Four "wow" features: trust card, blast-radius map, agent-instruction aggregation,
  heuristic setup-chain view.
- ~25 rules across all categories.
- Output: terminal (rich), JSON (stable schema), Markdown report.
- Four example repos doubling as integration fixtures and demo material.

## Out of scope (designed for, built later, each its own spec → plan → build cycle)

- Web app (Next.js), FastAPI backend, Postgres scan history / dashboard.
- GitHub Action, shields.io badge.
- AI explanation summaries (Ollama/API).

The engine exposes a stable `ReportModel` + JSON schema so every later front-end
imports `scanner_core` directly — no engine rewrite.

## Language / runtime / packaging

- **Python.** Distributed via `uvx` (modern, install-free equivalent of `npx`):
  `uvx agent-repo-preflight scan <path-or-url>`.
- Shipped as a **single installable Python distribution** (`agent_repo_preflight`)
  with internal sub-packages (`scanner_core`, `cli`, `report_renderer`). Not a
  multi-distribution monorepo; can be split later if the web app needs it.
- `pyproject.toml` defines the `agent-repo-preflight` console entry point.

## Architecture — 6-stage pipeline

```
acquire → load FileTree → detectors emit Facts → rules emit Findings
       → chain builder (heuristic) → score + verdict → ReportModel → renderers
```

### Stage 1 — Acquisition (`scanner_core/acquire`)
- Local path: walk the folder into an in-memory `FileTree`.
- GitHub URL: resolve to codeload `.tar.gz`, download, extract to a temp dir with
  **size cap** (total bytes) and **file-count cap**; build `FileTree`; delete temp.
- `FileTree` = list of `FileEntry{path, text, size, is_binary}`. Binary/oversized
  files are recorded by path but not scanned for content.
- No git invocation; no install/build/script execution at any point.
- Optional `GITHUB_TOKEN` env for private repos / higher rate limits; public works unauthenticated.

### Stage 2 — Detectors (`scanner_core/detectors`)
Each detector consumes the `FileTree` and emits typed **Facts**. Planned set:
- **PackageJsonDetector** — npm lifecycle scripts (`preinstall`, `postinstall`,
  `prepare`, `install`), and their command strings.
- **PythonInstallDetector** — `setup.py` custom commands / network calls,
  `pyproject.toml` build hooks.
- **ShellScriptDetector** — `install.sh`, `*.ps1`, `*.bat`, `Makefile` content.
- **ContentPatternDetector** — regex sweep across text files:
  `curl … | bash`, `wget … | sh`, `Invoke-WebRequest`, `Start-Process`, `nc`,
  `socat`, `chmod +x`, encoded PowerShell (`-enc`/`-EncodedCommand`),
  `base64 -d | sh`, DNS TXT lookups, `/dev/tcp`, credential-path reads.
- **AgentInstructionDetector** — presence + excerpt of `CLAUDE.md`,
  `.cursor/rules`, `.windsurf`/`.windsurfrules`, `.github/copilot-instructions.md`,
  MCP config files (`.mcp.json`, `mcp.json`, etc.), including tool/permission grants.
- **SecretsEnvDetector** — `.env.example` requesting broad tokens; scripts reading
  `~/.ssh`, `~/.aws`, `.npmrc`, `.pypirc`, browser credential paths, GitHub tokens.
- **GitHubActionsDetector** — workflow `permissions: write-all`, unpinned actions
  (no SHA), `pull_request_target`, execution on untrusted PRs.

A **Fact** = `{type, file, line, data{...}}`. Detectors do detection-by-parsing;
they never decide severity (rules do).

### Stage 3 — Rule engine (`scanner_core/rules` + `rules/*.yaml`)
- Rules are declarative YAML. A rule matches against Fact `type` + `data` fields
  and/or raw content `patterns` + `file_patterns`.
- A matched rule produces a **Finding**:
  `{rule_id, severity, category, file, line, evidence, explanation, remediation, blast_radius[]}`.
- Rule loader validates schema at startup; bad rules fail loudly (not silently skipped).

### Stage 4 — Setup-chain builder (`scanner_core/chains`) — heuristic
- Links Facts/Findings into ordered "chain of trust" steps, e.g.
  `README: "run npm install" → package.json postinstall → scripts/setup.js → fetch(remote) → base64 decode → shell exec`.
- Best-effort reference resolution (script paths, URLs). **Explicitly labeled
  heuristic**; when a link can't be resolved it shows what it found and stops,
  rather than fabricating. Never blocks the rest of the report.

### Stage 5 — Scoring + verdict (`scanner_core/score`)
- Each severity has a weight: `info|low|medium|high|critical`.
- **Verdict:**
  - **FAIL** — any `critical` finding, **or** any install-time network+exec chain.
  - **REVIEW** — any `high` or `medium` finding (no FAIL trigger).
  - **PASS** — only `low`/`info` or no findings.
- **Blast-radius rollup** — per capability
  (`filesystem, network, secrets, shell, install_hooks, ci`), each rated
  HIGH/MED/LOW from the max severity of findings tagged to it.
- Deterministic and documented; no randomness, no LLM in the scoring path.

### Stage 6 — Report model + renderers (`scanner_core/model`, `report_renderer`)
- One `ReportModel` (below) feeds all renderers.
- Renderers: **terminal** (rich, the default), **JSON** (`--json`, stable schema),
  **Markdown** (`--markdown-report`).

## Key interface — `ReportModel`

The contract every later front-end (web/API/Action) reuses:

```
ReportModel
  schema_version
  repo { source, name, ref, scanned_at }
  verdict                # PASS | REVIEW | FAIL
  score                  # numeric
  findings[] {
    rule_id, severity, category, file, line,
    evidence, explanation, remediation, blast_radius[]
  }
  blast_radius { filesystem, network, secrets, shell, install_hooks, ci }
  agent_instructions[] { surface, file, content_excerpt }
  chains[] { steps[] { kind, file, line, detail } }
  stats { rules_run, files_scanned, files_skipped }
  disclaimer
```

## Rule YAML schema (contributor surface)

```yaml
id: node-postinstall-network-exec
name: Install script may run remote/dynamic code
severity: high                       # info | low | medium | high | critical
category: install-hooks
blast_radius: [network, shell, install_hooks]
match:
  facts: [pkg.lifecycle_script]      # detector-emitted fact types
  patterns: ["curl", "wget", "node -e", "base64"]   # regex over the fact/evidence text
  file_patterns: ["package.json"]    # optional path filter
explanation: "Install lifecycle script may execute remote or dynamic code."
remediation: "Inspect the referenced script; run install with --ignore-scripts."
references: ["https://..."]
```

## CLI surface

```
agent-preflight scan .                      # local folder, terminal report
agent-preflight scan https://github.com/o/r # remote, tarball-fetched
agent-preflight scan . --json               # machine-readable
agent-preflight scan . --markdown-report    # markdown file/stdout
agent-preflight rules                        # list loaded rules
```

Exit codes: `0` PASS, `1` REVIEW, `2` FAIL (CI-friendly), distinct code for tool errors.

## Testing strategy (TDD throughout)

- **Detector unit tests** — each detector against tiny fixture files; assert exact Facts.
- **Rule engine tests** — rules against synthetic Facts; assert Findings.
- **Scoring tests** — synthetic finding sets → asserted verdict + blast-radius.
- **Integration / snapshot** — the four example repos
  (`clean`, `suspicious-node`, `suspicious-python`, `suspicious-mcp`) scanned
  end-to-end with asserted verdicts. These are simultaneously the demo material
  and the regression suite.
- **Acquisition tests** — local walk; tarball extraction against a saved fixture
  tarball (no live network in tests).

## Repo layout (v1 populates a subset of the eventual full tree)

```
agent-repo-preflight/
  packages/scanner_core/   # acquire, detectors, rules engine, chains, score, model
  packages/cli/            # argument parsing + render dispatch
  packages/report_renderer/
  rules/                   # ~25 YAML rules
  examples/{clean,suspicious-node,suspicious-python,suspicious-mcp}/
  docs/{threat-model,rule-authoring,ai-agent-safety-checklist}.md
  pyproject.toml           # uvx entry point: agent-preflight / agent-repo-preflight
  tests/
```

## Non-goals / explicit honesty

- Never executes target repo code.
- Never asserts a repo is "safe"; reports presence/absence of risk indicators only.
- No LLM in the detection or scoring path (deterministic rules only). AI, if ever
  added, explains findings — it never produces them.
