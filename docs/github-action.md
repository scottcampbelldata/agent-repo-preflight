# GitHub Action reference

`agent-repo-preflight` ships a composite GitHub Action that scans a repository for
AI-agent execution risks, comments on PRs, and gates the check.

## Usage

```yaml
name: Agent Preflight
on: [pull_request]
permissions:
  contents: read
  pull-requests: write
jobs:
  preflight:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: scottcampbell/agent-repo-preflight@v1
        with:
          path: "."
          fail-on: "FAIL"
          comment: "true"
```

## Inputs

| Input | Default | Description |
|---|---|---|
| `path` | `.` | Directory to scan (the checked-out workspace). |
| `fail-on` | `FAIL` | Verdict that fails the check: `FAIL`, `REVIEW`, or `none`. |
| `comment` | `true` | Post/update a sticky PR comment with the Markdown report. |
| `github-token` | `${{ github.token }}` | Token used to post the PR comment. |

## Outputs

| Output | Description |
|---|---|
| `verdict` | `PASS`, `REVIEW`, or `FAIL`. |
| `score` | Numeric risk score. |
| `report-json` | Path to the JSON report (`preflight-report.json`). |

The Action also writes `preflight-badge.json` (a shields.io endpoint payload) and
`preflight-report.md` (the comment body) into the workspace, so you can upload them as
artifacts or publish the badge.

## Permissions

The Action needs only:

```yaml
permissions:
  contents: read          # read the checked-out code
  pull-requests: write    # post the PR comment (omit if comment: "false")
```

It never requests `write-all` — consistent with what the scanner itself flags as a CI
risk — and pins the actions it uses to full commit SHAs.

## Gating behavior

| `fail-on` | PASS | REVIEW | FAIL |
|---|---|---|---|
| `none` | pass | pass | pass |
| `REVIEW` | pass | **fail** | **fail** |
| `FAIL` (default) | pass | pass | **fail** |

## How it works

1. Sets up Python and installs its own bundled copy of the package
   (`pip install "$GITHUB_ACTION_PATH"`), so it works without a PyPI release and always
   matches the pinned action ref.
2. Runs `agent-repo-preflight scan <path> --json --badge preflight-badge.json` and a
   second `--markdown-report` pass for the comment body. The scanner never executes
   target repository code.
3. Upserts a sticky PR comment (edits its previous comment instead of spamming).
4. Exits nonzero when the verdict meets the `fail-on` threshold.

## Outputs example

```yaml
      - uses: scottcampbell/agent-repo-preflight@v1
        id: preflight
        with:
          fail-on: none
      - run: echo "Verdict was ${{ steps.preflight.outputs.verdict }} (score ${{ steps.preflight.outputs.score }})"
```

## Notes

- The repo running this project's own CI uses `fail-on: none`, because it intentionally
  ships malicious example fixtures under `examples/`.
- For self-hosted runners, ensure Python 3.11+ is available.
