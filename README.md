# Heads-Up Poker — Research Simulation

Educational R&D project in **adversarial decision-making under uncertainty**. This repository simulates a simplified heads-up poker environment for comparing bot policies (random, hand-strength heuristic, Monte Carlo equity, preliminary MCCFR).

> **Disclaimer:** This is **not** a trading system, financial alpha, or production poker product. Historical experiment summaries are **provisional** until the corrected engine is rebuilt and benchmarks are rerun from versioned manifests.

## Architecture

```text
cpp_engine/          C++ rules, evaluator, simulator (pybind11)
poker_ai/            Python bots and CFR training code
ui/                  Flask research demo (local use)
experiments/         Manifests, runner, generated runs (ignored)
tests/               pytest unit, integration, property, regression
docs/                Canonical game rules and methodology notes
```

The **C++ engine** is the intended source of truth for dealing, betting, and showdown. The Flask UI implements a parallel state machine for human play and will be refactored to call the engine directly.

## Quick start

### 1. Environment

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate

pip install -e ".[dev,experiments]"
```

### 2. Build native module

**CMake (preferred):**

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build
```

**Fallback (Windows, MSVC in PATH):**

```bash
python build_simple.py
```

Verify:

```bash
python -c "from poker_ai import poker_engine; print(poker_engine.__version__)"
```

### 3. Run tests

```bash
pytest
```

Tests skip automatically if `poker_engine` is not built.

### 4. Run an experiment from a manifest

```bash
python experiments/test_cpp_v2_bot.py --manifest experiments/manifests/v2_vs_v0_baseline.json
```

Outputs are written to `experiments/runs/<name>_<timestamp>/` (git-ignored) with:

- `matches.csv` — per-match results
- `summary.json` — aggregates + provenance (Git commit, seeds, hashes)
- `manifest_resolved.json` — replayable configuration

Replay:

```bash
python experiments/test_cpp_v2_bot.py --replay experiments/runs/<run>/summary.json
```

### 5. Web demo (local)

```bash
python ui/app.py
```

Open http://localhost:5000 — research demo only; debug mode must stay local.

## Bot versions

| ID | Name           | Description                                      |
|----|----------------|--------------------------------------------------|
| v0 | Random         | Uniform random legal actions                     |
| v1 | HandStrength   | Preflop/table-strength heuristic                   |
| v2 | MonteCarlo     | Monte Carlo equity + threshold policy            |
| v3 | Experimental CFR | Small tabular CFR policy; not a GTO claim      |

See [docs/game-rules.md](docs/game-rules.md) for the exact simplified rules under test.

## Documentation

- [Game rules](docs/game-rules.md) — canonical engine specification
- [Reproducibility](docs/reproducibility.md) — manifests, seeds, provenance
- [Original R&D Poker PDF](docs/r-and-d-poker.pdf) — preserved project artifact
- [PDF status](docs/r-and-d-poker-status.md) — why its historical results are provisional
- [IMPROVEMENT_PLAN.md](IMPROVEMENT_PLAN.md) — engineering roadmap

## Status

Priority 0 correctness work is in progress:

- Single-deck dealing (nine unique cards per hand)
- Postflop BB-first action order
- Per-street raise cap and all-in refunds
- pytest suite and manifest-based experiments

**Do not cite paper headline numbers** until experiments are regenerated after these fixes.

## License

MIT — see LICENSE (to be added).
