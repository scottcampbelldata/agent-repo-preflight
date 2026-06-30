# Releasing

Publishing is automated via `.github/workflows/release.yml`, which builds and uploads to
PyPI using **Trusted Publishing** (OIDC) — no API token is stored in the repo.

## One-time setup on PyPI

1. Create the project on PyPI (or reserve the name `agent-repo-preflight`).
2. In the project's **Publishing** settings, add a GitHub Actions trusted publisher:
   - Owner: `scottcampbell` (your GitHub org/user)
   - Repository: `agent-repo-preflight`
   - Workflow name: `release.yml`
   - Environment: `pypi`
3. In the GitHub repo settings, create an **Environment** named `pypi` (optionally add
   required reviewers so a release needs approval).

## Cutting a release

1. Bump the version in `pyproject.toml` (e.g. `0.1.0` → `0.2.0`).
2. Move the `Unreleased` notes into a new dated section in `CHANGELOG.md`.
3. Commit:

   ```bash
   git commit -am "release: v0.2.0"
   ```

4. Tag and push — this triggers the release workflow:

   ```bash
   git tag v0.2.0
   git push origin main --tags
   ```

The workflow builds the sdist + wheel, runs `twine check`, and publishes to PyPI. After
it succeeds, `uvx agent-repo-preflight` and `pip install agent-repo-preflight` work for
everyone.

## Verifying

```bash
pipx run agent-repo-preflight scan https://github.com/expressjs/express
# or
uvx agent-repo-preflight rules
```

## Versioning

- **patch** (`0.1.x`): bug fixes, new rules that don't change existing verdicts materially.
- **minor** (`0.x.0`): new features (detectors, CLI flags, web/action capabilities).
- **major** (`x.0.0`): breaking changes to the JSON report schema or CLI contract. Bump
  the report `schema_version` alongside.
