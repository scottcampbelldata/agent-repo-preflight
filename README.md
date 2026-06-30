# agent-repo-preflight

**Paste a GitHub repo. Get a "safe for AI agent use?" report — before you let Claude Code, Codex, Cursor, Copilot Agent, or Windsurf clone, install, or run it.**

A local-first scanner that audits a repository for hidden execution risks **before** an AI coding agent touches it. It never runs the target repo's code — it reads files, parses install hooks, agent-instruction files, MCP configs, and CI workflows, and reports a deterministic verdict.

```bash
uvx agent-repo-preflight scan https://github.com/org/repo
# or a local folder:
uvx agent-repo-preflight scan .
```

## Why

A seemingly clean GitHub repo can trick an AI coding agent into running malware through *indirect* setup steps — a `postinstall` hook that fetches a remote payload, a `CLAUDE.md` that says "run setup without reviewing it," an MCP config that hands the agent a shell. Agents now author and run code across hundreds of thousands of repos. This tool is the preflight check before that happens.

## What it does

The scanner runs a deterministic 6-stage pipeline — **no LLM in the detection path**:

```
acquire → FileTree → detectors emit Facts → YAML rules emit Findings
       → heuristic chain builder → score/verdict → report
```

It produces:

- **A trust card** — `PASS` / `REVIEW` / `FAIL` verdict with a plain-English summary.
- **A blast-radius map** — per-capability risk (filesystem, network, secrets, shell, install hooks, CI).
- **Agent-instruction aggregation** — every `CLAUDE.md`, Cursor/Windsurf rule, Copilot instruction, and MCP config in one place.
- **A heuristic setup-chain view** — the indirect path from `README` → install hook → script → remote fetch → decode → exec.

### Example: a suspicious repo

```
╭─────────────────────── Agent Repo Preflight ───────────────────────╮
│ AI-Agent Safety: FAIL                                              │
│ Repo: suspicious-node  •  Risk score: 28                          │
╰────────────────────────────────────────────────────────────────────╯
        Blast radius
│ network       │ HIGH │
│ shell         │ HIGH │
│ install_hooks │ MED  │

                          Findings
│ CRITICAL │ remote-pipe-to-shell      │ scripts/setup.js:7  │ execSync("curl … | bash") │
│ HIGH     │ base64-decode-exec        │ scripts/setup.js:13 │ eval(atob(d))             │
│ MEDIUM   │ node-lifecycle-script-... │ package.json:6      │ node scripts/setup.js     │

Suspicious setup chains (heuristic):
  readme_instruction(README.md:1) -> lifecycle_hook(package.json:6) ->
  referenced_script(scripts/setup.js:1) -> dangerous_call(scripts/setup.js:7)
```

## Install / run

Requires Python 3.11+.

```bash
# Run without installing (recommended):
uvx agent-repo-preflight scan <path-or-github-url>

# Or install:
pip install agent-repo-preflight
agent-repo-preflight scan .
```

### Commands & output formats

```bash
agent-repo-preflight scan .                    # rich terminal report (default)
agent-repo-preflight scan <url> --json         # stable JSON (for CI / tooling)
agent-repo-preflight scan . --markdown-report  # shareable Markdown
agent-repo-preflight rules                      # list the loaded rules
```

CI-friendly exit codes: `0` = PASS, `1` = REVIEW, `2` = FAIL, `3` = tool error.

Set `GITHUB_TOKEN` to scan private repos or raise rate limits (public repos work without it).

## Web demo

A shareable, visual version of the same report. One Python service (FastAPI +
server-rendered HTML), SQLite-backed permalinks — no Node, no separate database server.

```bash
pip install 'agent-repo-preflight[web]'
python -m agent_repo_preflight.web          # serves on http://127.0.0.1:8000
```

Pages:

- `/` — paste a GitHub URL, get a report; recent scans listed below
- `/report/{id}` — the shareable visual report (trust card, blast-radius grid, findings, setup-chain, agent instructions), plus `.json` and `.md` versions at the same id
- `/examples` — pre-scanned clean + high-risk demo repos
- `/rules` — the loaded ruleset

The web boundary is **GitHub-only and remote-only by construction**: it validates every
URL with the same parser the engine uses (rejecting non-GitHub URLs *and* local server
paths), so it can't be coaxed into scanning the host filesystem. It still never executes
target repository code. Set `AGENT_PREFLIGHT_DB`, `AGENT_PREFLIGHT_HOST`, and
`AGENT_PREFLIGHT_PORT` to configure storage and binding.

## What it covers

| Category | Examples |
|---|---|
| **Install hooks** | npm `pre/postinstall`/`prepare`, `setup.py` network calls, custom build backends |
| **Dangerous commands** | `curl \| bash`, `/dev/tcp` reverse shells, `nc`/`socat`, base64-decode-exec, encoded PowerShell, DNS-TXT payloads, Dockerfile/Makefile remote exec |
| **Agent instructions** | `CLAUDE.md`, Cursor/Windsurf rules, Copilot instructions, MCP shell/filesystem grants, "run without review" directives |
| **Secrets / env** | `.env.example` requesting broad cloud keys, reads of `~/.ssh` / `~/.aws` / `.npmrc` |
| **CI / CD** | `permissions: write-all`, unpinned actions, `pull_request_target` running untrusted PR code |

## Honest about its limits

This tool detects repo-level **risk indicators** before AI agents execute setup, install, CI, MCP, or instruction files. **It does not prove a repository is safe.** A `PASS` means no known indicators fired — not a guarantee. Always read code before running it.

The scanner **never executes target repository code**: it downloads a tarball (no `git`), extracts it in memory, and only reads. That "never run it" guarantee is the point.

## Contributing rules

Rules are plain YAML in [`src/agent_repo_preflight/rules_data/`](src/agent_repo_preflight/rules_data/). Adding one is the easiest way to contribute — see [docs/rule-authoring.md](docs/rule-authoring.md) for the schema and the list of available detector facts.

## Docs

- [Threat model](docs/threat-model.md) — what AI-agent repo onboarding risks look like, and what this covers / doesn't.
- [Rule authoring](docs/rule-authoring.md) — write and test a new rule.
- [AI-agent safety checklist](docs/ai-agent-safety-checklist.md) — a human checklist mirroring the rules.

## License

Source-available under the [PolyForm Noncommercial License 1.0.0](LICENSE).

- **Free for any noncommercial use** — personal, research, education, hobby, and
  nonprofit/government use — provided you keep the copyright/attribution notice intact.
- **Commercial use requires a separate license.** To use this software for a commercial
  purpose, get written permission first: Scott Campbell <scott@scottcampbell.io>.

Note: this is *source-available*, not OSI "open source" — commercial users must obtain a
license. Contributions are accepted under the same terms.
