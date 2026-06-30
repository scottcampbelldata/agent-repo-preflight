# AI-agent repo safety checklist

A human checklist for vetting an unfamiliar repository before letting an AI coding agent
clone, install, or run it. Mirrors what `agent-repo-preflight` checks automatically — use
it to confirm and to catch what static rules can't.

## Before the agent touches the repo

- [ ] Run `agent-repo-preflight scan <url>` and read the verdict and findings.
- [ ] Clone into an **isolated** environment (container/VM), not your primary machine.
- [ ] Plan to install with execution disabled first: `npm install --ignore-scripts`,
      inspect, then enable.

## Install hooks

- [ ] `package.json` — any `preinstall` / `postinstall` / `prepare` scripts? Read them.
- [ ] `setup.py` — any network calls, `os.system`, `subprocess`, or `exec`/`eval`?
- [ ] `pyproject.toml` — is the `build-backend` a recognized project?
- [ ] Shipped `install.sh` / `*.ps1` / `*.bat` / `Makefile` — read every target.

## Dangerous command patterns

- [ ] No `curl … | bash` or `wget … | sh` (remote-pipe-to-shell).
- [ ] No `/dev/tcp/…`, `nc -e`, `ncat`, or `socat` (reverse shells).
- [ ] No `base64 -d | sh`, `eval(atob(…))`, or `powershell -enc` (obfuscated exec).
- [ ] No DNS TXT lookups in setup scripts (covert payload channel).
- [ ] No `url.<x>.insteadOf` git rewrites pointing at unfamiliar hosts.

## Agent instructions

- [ ] Read every `CLAUDE.md`, `.cursor/rules`, `.windsurfrules`, and
      `.github/copilot-instructions.md`.
- [ ] Reject any "run X without reviewing it" directive — that is a prompt-injection.
- [ ] Review MCP configs: does any server grant `shell` / `filesystem` / `exec`?

## Secrets & environment

- [ ] Does `.env.example` ask for broad cloud keys, tokens, or private keys? Provide only
      narrowly-scoped, disposable credentials.
- [ ] Does any script read `~/.ssh`, `~/.aws`, `.npmrc`, `.pypirc`, or browser data?

## CI / CD

- [ ] No `permissions: write-all`; scope tokens per job.
- [ ] Third-party actions pinned to full commit SHAs.
- [ ] No `pull_request_target` workflow that checks out and runs untrusted PR code.

## Remember

A clean scan and a completed checklist reduce risk; they do not prove safety. When in
doubt, read the code and run it sandboxed.
