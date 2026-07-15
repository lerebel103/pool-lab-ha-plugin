# Agent Guidelines

## Git Policy

**Never commit, push, or interact with git in any way without explicit user permission.**
This includes but is not limited to: `git add`, `git commit`, `git push`, `git stash`, `git reset`, `git checkout`, `git branch`, creating tags, or any other git operation.

**Always ask first.** Even when the user says "push" or "commit", confirm the exact action before executing. Do not chain git operations (e.g. commit + push + tag) without listing each step and receiving approval. The user must grant permission for each distinct git action or explicitly approve a sequence.

## Code Quality

- All Python code must pass `ruff` linting and formatting checks before being considered complete.
- Run `make lint` to check for issues and `make format` to auto-fix formatting.
- Follow the existing code style: type hints, docstrings, and `from __future__ import annotations` at the top of every module.
- Keep imports sorted (enforced by ruff).

## Project Structure

- Integration code lives in `custom_components/pool_lab/`.
- Protocol specifications live in `docs/protocol.md`. Always refer to this document when implementing or modifying protocol-level code (commands, parsing, field formats) to ensure consistency with the device behavior.
- Do not add files outside this structure unless they are project-level config (Makefile, pyproject.toml, README, etc.).
- Do not introduce new dependencies without discussing it first.

## Testing

- Tests go in the `tests/` directory.
- Use `pytest` with `pytest-asyncio` for async tests.
- Run tests with `make test`.

## Versioning

- The git tag is the **single source of truth** for the version.
- `manifest.json` contains `"version": "0.0.0"` as a dev placeholder. Do not manually update this value.
- `pyproject.toml` has no `version` field — it is not needed for a HA integration.
- The release workflow (`.github/workflows/release.yml`) stamps the real version from the tag into `manifest.json` before creating the release zip.
- To release: push a semver tag (e.g. `v0.5.0`) to `main`. The workflow handles the rest.
