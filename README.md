# Heads-Up Poker Bot

Four poker bots, one C++ engine, and a benchmark harness that makes every match replayable from a seed. Built to study decisions under uncertainty during an exchange at Hogeschool van Amsterdam (Fall 2025).

> Status: the C++ engine, three bots and the benchmark harness are done and covered by CI on Linux and Windows. The CFR bot is experimental: it still loses to the simpler Monte Carlo bot, and the section below explains why.

## Results

Each row is 200 matches of up to 100 hands (10 seeds × 20 matches), stack 1,000, blinds 10/20. "A wins" is the share of matches the first bot won, with a 95% interval.

| Matchup | A wins | 95% interval | Hands played |
|---|---:|---:|---:|
| HandStrength vs Random | 97.5% | 94.3%–98.9% | 15,289 |
| Monte Carlo vs Random | 97.0% | 93.6%–98.6% | 17,728 |
| Monte Carlo vs HandStrength | 72.5% | 65.9%–78.2% | 16,906 |
| **Monte Carlo vs CFR** | **98.0%** | 95.0%–99.2% | 14,133 |
| Monte Carlo vs Monte Carlo (control) | 49.0% | 42.2%–55.9% | 19,599 |

Every bot beats random, and Monte Carlo beats the heuristic bot about 3 times in 4. Self-play lands near 50%, and swapping seats flips each result, so the engine doesn't favour either seat.

**The CFR bot loses.** CFR is the algorithm behind superhuman poker AIs, and here it loses 98% of matches to a bot that just simulates 100 random opponent hands per decision. Training longer didn't help either: a 20,000-iteration strategy with 42,648 information sets won 3 of 50 matches against Monte Carlo. The bottleneck is the card abstraction and how states map between training and play, not the number of iterations. Full numbers are in [docs/benchmark-status.md](docs/benchmark-status.md).

## The bots

| ID | Bot | How it decides |
|---|---|---|
| v0 | Random | Picks a uniformly random legal action. The baseline. |
| v1 | HandStrength | Scores its hand preflop and against the board, then acts on thresholds. |
| v2 | Monte Carlo | Postflop, deals the opponent's unknown cards many times (300 by default, 100 in the benchmarks) to estimate equity, then acts on thresholds. |
| v3 | CFR (experimental) | Plays a strategy from a small tabular Monte Carlo counterfactual regret minimization (MCCFR) trainer. |

To add a bot, start from [docs/bot-template.py](docs/bot-template.py).

## How it works

```
manifest.json --> run_benchmark.py --> poker_engine (C++, pybind11) --> matches.csv + summary.json
 (bots, seeds,          |                 |- deal: one 52-card deck, 9 unique cards
  stacks, blinds)       |                 |- betting: preflop + one postflop round
                        |                 '- showdown: hand evaluator
                        '- poker_ai/bots: v0-v3 decide each action
```

- **The game is simplified on purpose.** There are two betting rounds: preflop, then a single postflop round with all five board cards dealt at once. That keeps hidden information, position and betting pressure while making experiments small enough to repeat on a laptop. The exact rules are in [docs/game-rules.md](docs/game-rules.md).
- **The engine is the single source of truth.** Dealing, betting, all-in refunds and showdown run in C++ and are exposed to Python through pybind11.
- **Every run can be replayed.** A versioned JSON manifest fixes the bots, seeds, stacks and blinds. Each run records the Git commit, the platform and hashes of its output files, and `--replay` reruns it from its summary. See [docs/reproducibility.md](docs/reproducibility.md).
- **The rules are tested, not assumed.** pytest covers unit, integration, regression and property-based tests, and the property tests (Hypothesis) check that every deal uses nine unique cards, chips are never created or lost, and stacks never go negative.

## Run it

Needs Python 3.10+, CMake and a C++ compiler.

```bash
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -e ".[dev,experiments]"
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build
pytest
```

On Windows with MSVC on the PATH, `python build_simple.py` also builds the engine.

Run a benchmark, then replay it:

```bash
python experiments/run_benchmark.py --manifest experiments/manifests/v2_vs_v0_baseline.json
python experiments/run_benchmark.py --replay experiments/runs/<run>/summary.json
```

Play against the bots, or watch them play each other, in the local web demo:

```bash
python ui/app.py   # http://localhost:5000
```

## Limits

- Results only hold for this two-round game. They say nothing about full Hold'em, and nothing about markets.
- Monte Carlo rollouts are CPU-bound, so the large benchmarks take minutes to hours on a laptop.
- v3 stays labelled experimental until it passes a proper exploitability check against known equilibria. The Kuhn and Leduc toy-game harness (`experiments/validate_toy_cfr.py`) is a first step.

The roadmap is in [IMPROVEMENT_PLAN.md](IMPROVEMENT_PLAN.md).
