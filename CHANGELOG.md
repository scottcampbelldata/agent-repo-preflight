# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/), and this project adheres to
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- Scanner engine: tarball acquisition (never executes target code), seven detectors,
  25 YAML rules, scoring/verdict, blast-radius rollup, and a heuristic setup-chain view.
- CLI: `scan` (terminal / `--json` / `--markdown-report` / `--badge`) and `rules`,
  with CI-friendly exit codes.
- Web demo: FastAPI + server-rendered reports, SQLite-backed shareable permalinks,
  `/examples` and `/rules` pages.
- GitHub Action: composite action that scans PRs, posts a sticky comment, writes a
  badge, and gates the build via `fail-on`.
- Badge: shields.io static + dynamic endpoint support.
- Packaging: PyPI-ready metadata and an OIDC trusted-publishing release workflow.
- Deployment: Docker image, Docker Compose, and a VPS deploy guide.

## [0.1.0] - unreleased

Initial release.
