# Contributing

Thank you for helping improve this research codebase.

## Development setup

1. Clone the repository and create a virtual environment.
2. Install dev dependencies: `pip install -e ".[dev,experiments]"`.
3. Build the C++ engine (CMake or `build_simple.py`).
4. Run `pytest` before opening a pull request.

## Commit messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

- `fix(engine): deal all cards from one deck`
- `test: add chip conservation property tests`
- `docs: document raise cap per street`

## Scope

- Keep changes focused; avoid unrelated refactors in correctness PRs.
- Do not update paper headline results until experiments are rerun from manifests.
- Do not frame poker benchmarks as financial or trading performance.

## Pull requests

- Describe rule/engine changes and link to `docs/game-rules.md` updates.
- List tests run and note if the native module was rebuilt.
- Ensure CI passes (GitHub Actions).
