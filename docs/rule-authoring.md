# Authoring rules

Rules are plain YAML files in `src/agent_repo_preflight/rules_data/`, one rule per file.
The engine loads and validates every `*.yaml` there at startup; an invalid rule fails
loudly rather than being silently skipped.

## Schema

```yaml
id: node-postinstall-network-exec        # unique, kebab-case
name: Install lifecycle script may run remote or dynamic code
severity: critical                        # info | low | medium | high | critical
category: install-hooks                   # free-text grouping label
blast_radius: [network, shell, install_hooks]   # subset of the 6 capabilities
match:
  facts: [pkg.lifecycle_script]           # detector fact types to match (optional)
  patterns: ["curl", "wget", "base64"]    # regex, case-insensitive (optional)
  file_patterns: ["package.json"]         # path/basename globs (optional)
explanation: >
  Plain-English description of why this is risky.
remediation: >
  What the developer should do about it.
references:
  - "https://…"
```

Required fields: `id`, `name`, `severity`, `category`, `explanation`, `remediation`.
`blast_radius` capabilities must be one of:
`filesystem`, `network`, `secrets`, `shell`, `install_hooks`, `ci`.

## Two ways a rule matches

**1. Fact rule** — `match.facts` is set. The rule matches any detector Fact whose `type`
is in the list. If `match.patterns` is also given, at least one pattern must match the
fact's evidence or one of its `data` values. The Finding's file/line come from the Fact.

**2. Content rule** — `match.facts` is absent but `match.patterns` is set. The rule scans
every text file line-by-line (optionally filtered by `match.file_patterns`) and emits one
Finding per matching line.

Identical `(rule_id, file, line)` Findings are de-duplicated.

## Available detector facts

| Fact type | Emitted when | `data` keys |
|---|---|---|
| `pkg.lifecycle_script` | npm `pre/postinstall`, `prepare`, etc. | `hook`, `command` |
| `py.setup_network` | `setup.py` line does network/process/exec | — |
| `py.pyproject_build_hook` | non-standard PEP 517 build backend | `backend` |
| `content.<id>` | regex pattern hit in any text file | `pattern_id` |
| `shell.script_present` | repo ships `install.sh`/`*.ps1`/`*.bat`/`Makefile` | `kind` |
| `agent.instruction_file` | `CLAUDE.md`/Cursor/Windsurf/Copilot/MCP file present | `surface` |
| `agent.instruction_run_unverified` | "run … without … review" text | — |
| `agent.mcp_tool_grant` | MCP config references a powerful tool | `tool` |
| `secret.broad_env_request` | `.env.example` requests a broad secret | `key` |
| `ci.write_all_permissions` | workflow `permissions: write-all` | — |
| `ci.unpinned_action` | `uses:` not pinned to a 40-char SHA | `action` |
| `ci.pull_request_target` | workflow triggers on `pull_request_target` | — |
| `ci.untrusted_checkout_exec` | PR-target workflow checks out + runs PR code | — |

The `content.<id>` ids are: `curl_pipe_sh`, `wget_pipe_sh`, `invoke_webrequest`,
`start_process`, `netcat`, `socat`, `chmod_x`, `encoded_powershell`, `base64_exec`,
`dns_txt`, `dev_tcp`, `cred_path_read`.

## Adding a rule

1. Create `src/agent_repo_preflight/rules_data/<your-id>.yaml`.
2. If you need a new kind of detection that regex can't express (parsing a structured
   file, following references), add a **detector** in
   `src/agent_repo_preflight/scanner_core/detectors/` that emits a new Fact type, then
   reference it from your rule's `match.facts`.
3. Add a test. Detector tests live in
   `tests/scanner_core/detectors/`; end-to-end behavior can be asserted via a fixture
   repo under `examples/` and `tests/test_examples_integration.py`.
4. Run `python -m pytest -q`.

## Severity guidance

- **critical** — execution of attacker-controlled code at install/CI time, reverse shells.
- **high** — credential access, obfuscated execution, network payload retrieval.
- **medium** — capability grants, install hooks present, broad secret requests.
- **low** — hygiene issues (unpinned actions, `chmod +x`).
- **info** — surfaces worth a human glance (an instruction file exists).

A `critical` finding, or any install-hook finding tagged `network`, forces an overall
`FAIL`. Any `high`/`medium` forces at least `REVIEW`.
