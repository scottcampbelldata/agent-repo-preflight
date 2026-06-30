# Threat model: AI coding agents and repository onboarding

## The shift

AI coding agents (Claude Code, Codex, Cursor, Copilot Agent, Windsurf, Aider) routinely
clone unfamiliar repositories and then **install dependencies, run setup scripts, and
execute build/test commands** on the developer's machine — often with limited human
review of what those steps actually do. The repository is no longer just data the
developer reads; it is a set of instructions an autonomous agent may carry out.

This collapses a trust boundary. Code that previously only ran *after* a human chose to
run it can now run because an agent followed a `README`, a `CLAUDE.md`, or an install
lifecycle hook.

## Attacker goals

- **Code execution on the developer's host** at clone/install/build time.
- **Credential theft** (`~/.ssh`, `~/.aws`, `.npmrc`, `.pypirc`, browser login data, CI secrets).
- **Persistence / C2** via reverse shells or covert channels.
- **Supply-chain pivot** — using the compromised host or its tokens to attack downstream.

## Attack surfaces this scanner inspects

| Surface | Mechanism | Example |
|---|---|---|
| Install lifecycle hooks | Code runs automatically on `npm install` / `pip install` | `postinstall` that fetches and runs a remote payload |
| Indirect setup chains | README → hook → script → fetch → decode → exec | Each step looks innocuous in isolation |
| Dangerous shell patterns | Remote-pipe-to-shell, reverse shells, encoded commands | `curl … \| bash`, `/dev/tcp`, `powershell -enc`, `base64 -d \| sh` |
| Covert retrieval | DNS TXT payloads, URL rewriting | `dig TXT`, `url.<x>.insteadOf` |
| Agent-instruction injection | Files that steer agent behavior | `CLAUDE.md` saying "run setup without reviewing it" |
| MCP capability grants | Config hands the agent powerful tools | MCP server exposing `shell` / `filesystem` |
| Secrets solicitation | Env templates asking for broad credentials | `.env.example` requesting cloud keys |
| CI/CD abuse | Untrusted code running with secrets | `pull_request_target` checking out and running PR code |

## What the scanner does NOT do

- It **does not execute** the target repository's code — by design. It downloads a
  tarball (no `git`), extracts it in memory, and only reads files.
- It **does not prove safety.** It reports the presence or absence of known risk
  indicators. A determined attacker can write a payload that no static rule catches.
- It does **not** scan dependency *contents* (transitive packages pulled at install
  time), dynamic/obfuscated payloads fetched at runtime, or compiled binaries.
- It is **not** a sandbox or runtime monitor. Pair it with isolation (containers, VMs,
  `--ignore-scripts`) for actual execution.

## How to use it

Treat the verdict as triage, not a gate you can blindly trust:

- **FAIL** — do not run with an autonomous agent until a human reviews the flagged paths.
- **REVIEW** — read the findings; decide deliberately.
- **PASS** — no known indicators fired. Still read code before running it.
