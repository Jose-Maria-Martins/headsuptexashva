# Heads-Up Poker - Research Simulation

Educational R&D project in **adversarial decision-making under uncertainty**. This repository simulates a simplified heads-up poker environment for comparing bot policies (random, hand-strength heuristic, Monte Carlo equity, preliminary MCCFR).

> **Disclaimer:** This is **not** a trading system, financial alpha, or production poker product. Historical experiment summaries are **provisional** until the corrected engine is rebuilt and benchmarks are rerun from versioned manifests.

## Why heads-up poker?

Heads-up poker is a compact environment for studying adversarial decisions
under uncertainty. With only two players, it is easier to inspect action order,
position, bankroll changes, and strategy interactions than in a full table.
The project is an engineering and modelling exercise; poker performance does
not imply financial-market skill or alpha.

## Why this simplified game?

The engine intentionally uses two betting rounds: a preflop round and one
postflop round that reveals the complete five-card board. This keeps the state
space and runtime small enough for repeatable experiments on a normal laptop,
while retaining hidden information, betting pressure, position, and showdown
uncertainty. It is not full no-limit Hold'em and results must be interpreted
only within these documented rules.

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
python experiments/run_benchmark.py --manifest experiments/manifests/v2_vs_v0_baseline.json
```

Outputs are written to `experiments/runs/<name>_<timestamp>/` (git-ignored) with:

- `matches.csv` — per-match results
- `summary.json` — aggregates + provenance (Git commit, seeds, hashes)
- `manifest_resolved.json` — replayable configuration

Replay:

```bash
python experiments/run_benchmark.py --replay experiments/runs/<run>/summary.json
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

To add a new policy, start with [docs/bot-template.py](docs/bot-template.py)
and follow the hierarchy and standards in [docs/code-standards.md](docs/code-standards.md).

## Documentation

- [Game rules](docs/game-rules.md) — canonical engine specification
- [Reproducibility](docs/reproducibility.md) — manifests, seeds, provenance
- [Code hierarchy and standards](docs/code-standards.md) — where code belongs and how to extend it
- [Bot template](docs/bot-template.py) — starting point for a new policy
- [Benchmark status](docs/benchmark-status.md) — latest seeded controls and limitations
- [IMPROVEMENT_PLAN.md](IMPROVEMENT_PLAN.md) — engineering roadmap

## Resource and time limitations

The project is deliberately sized for local research rather than a compute
cluster. Monte Carlo rollouts are CPU-bound, native builds require a C++ toolchain,
and large benchmarks can take minutes or hours depending on rollout count and
hardware. Results therefore report actual hands and runtime, and should not be
compared with production-scale poker solvers. The simplified game and smaller
experiments are engineering trade-offs for reproducibility and explainability.

## Status

Current status:

- Single-deck dealing (nine unique cards per hand)
- Postflop BB-first action order
- Per-street raise cap and all-in refunds
- 31-test pytest suite and manifest-based experiments
- larger mirror and seat-swapped benchmark matrix completed locally
- v3 remains experimental; toy-game validation is exploratory and does not yet
  justify a full Hold'em CFR claim

**Do not cite paper headline numbers** until experiments are regenerated after these fixes.
