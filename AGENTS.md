# Agent Guidelines

## Git Policy

**Never commit, push, or interact with git in any way without explicit user permission.**
This includes but is not limited to: `git add`, `git commit`, `git push`, `git stash`, `git reset`, `git checkout`, `git branch`, creating tags, or any other git operation. Always ask first.

## Code Quality

- All Python code must pass `ruff` linting and formatting checks before being considered complete.
- Run `make lint` to check for issues and `make format` to auto-fix formatting.
- Follow the existing code style: type hints, docstrings, and `from __future__ import annotations` at the top of every module.
- Keep imports sorted (enforced by ruff).

## Project Structure

- Integration code lives in `custom_components/pool_lab/`.
- Do not add files outside this structure unless they are project-level config (Makefile, pyproject.toml, README, etc.).
- Do not introduce new dependencies without discussing it first.

## Testing

- Tests go in the `tests/` directory.
- Use `pytest` with `pytest-asyncio` for async tests.
- Run tests with `make test`.
