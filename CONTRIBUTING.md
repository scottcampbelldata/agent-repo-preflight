# Contributing

Thanks for helping make AI-agent repo onboarding safer.

## Quick start

```bash
git clone <repo> && cd Repo-Preflight
python -m pip install -e ".[dev,web]" ruff
python -m pytest -q          # run the tests
ruff check src tests         # lint
ruff format src tests        # format
```

## The easiest contribution: a rule

Most detection lives in plain YAML under
[`src/agent_repo_preflight/rules_data/`](src/agent_repo_preflight/rules_data/).
Adding a rule is the lowest-friction way to improve coverage — see
[docs/rule-authoring.md](docs/rule-authoring.md) for the schema and the list of
detector facts you can match against.

## Project shape

- `scanner_core/` — the deterministic engine: acquire → detectors → rules → chains → score.
- `report_renderer/` — terminal / JSON / Markdown output.
- `web/` — the FastAPI demo (optional `[web]` extra).
- `rules_data/` — the YAML ruleset.
- `examples/` — intentionally unsafe demo repos that double as integration fixtures.

## Ground rules

- **Never make the scanner execute target repository code.** Acquisition is
  download-and-read only. No `subprocess` on target files, no `eval`/`exec`, no git.
- **Detection stays deterministic** — no LLM, no randomness in the scan path. (AI, if
  ever added, may *explain* findings; it must never *produce* them.)
- **Test-driven.** Add a failing test, then the code. Detector tests go in
  `tests/scanner_core/detectors/`; end-to-end behavior can be asserted via an
  `examples/` fixture.
- **Mind false positives.** A security tool that cries wolf gets ignored. If a pattern
  matches in documentation or test files, expect it to be downgraded (see
  `scanner_core/refine.py`). Validate new rules against a few real, benign repos.

## Before opening a PR

```bash
ruff check src tests && ruff format --check src tests && python -m pytest -q
```

All three must pass — CI runs the same gates.

## Licensing of contributions

This project is source-available under the
[PolyForm Noncommercial License 1.0.0](LICENSE): free for noncommercial use,
commercial use requires a separate license from the author. By submitting a
contribution, you agree it is licensed under the same terms.
