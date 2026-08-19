# Heads-Up Poker: Improvement and External-Readiness Plan

## Purpose and positioning

This repository is a promising educational R&D project in adversarial decision-making under uncertainty. It is **not yet an investable strategy, a trading system, or evidence of financial alpha**.

For an external hedge-fund audience, position it as a software and research-engineering case study. The credible story is:

- a controlled imperfect-information environment;
- reproducible experiments and rigorous testing;
- clear separation between a toy-game result and financial-market applicability;
- transparent limitations and a concrete technical roadmap.

Do not claim that poker results transfer directly to asset management. Any connection should be framed as practice in simulation, uncertainty, risk/reward trade-offs, reproducibility, and adversarial modelling.

## Current assessment

The repository currently contains:

- a C++ poker engine exposed to Python through `pybind11`;
- Python bot implementations: random (v0), rule-based hand strength (v1), Monte Carlo equity (v2), and preliminary MCCFR (v3);
- an experiment runner that writes CSV and JSON summaries;
- a Flask UI for bot-vs-bot and human-vs-bot demonstrations;
- a research paper describing the experiment and results.

The architecture has potential, but the implementation is currently difficult to trust, reproduce, and maintain. Correctness and reproducibility must be fixed before further strategic work or external sharing.

## Priority 0: Correctness blockers

These issues can undermine experiment validity and should be addressed before using or presenting historical results.

### 1. Community cards are dealt from a separate deck

`cpp_engine/src/simulator.cpp` deals hole cards by shuffling one deck and deals the board by shuffling a new deck. A community card can therefore duplicate either player's hole card.

Required change:

- Model one shuffled 52-card deck per hand.
- Deal player 0 cards, player 1 cards, and board cards from that same deck.
- Add a test asserting that every simulated hand has exactly nine unique cards.

### 2. Game rules disagree with the paper

The source and paper do not yet describe one consistent game.

| Topic | Current issue | Required decision |
|---|---|---|
| Raise cap | The simulator resets `max_raises` per betting round; the paper describes three raises per hand. | Specify whether the cap is per hand or per street; enforce and document one rule. |
| Postflop order | The simulator starts player 0 in every betting round; the paper says the big blind acts first postflop. | Encode and test the action-order rule for each street. |
| All-ins | Partial calls and unmatched bets are not clearly handled as real poker accounting. | Define side-pot/uncalled-bet behaviour for heads-up all-ins, then test it. |
| UI versus engine | The UI implements a second poker state machine. | Use the engine as the single source of truth or add strict contract tests. |

Create a concise `docs/game-rules.md` before changing behaviour. It should define blind posting, action order, legal actions, betting sizes, cap scope, all-in handling, pot settlement, odd chips, and showdown.

### 3. Reproducibility is not implemented end-to-end

`experiments/test_cpp_v2_bot.py` derives seeds from the current wall-clock time. That makes exact reruns impossible despite the paper's reproducibility claims.

Required change:

- Accept an explicit seed list or seed-manifest file.
- Save all seed values in every experiment artifact.
- Record Git commit, dirty/clean status, Python version, compiler, platform, package versions, engine hash, and bot configuration.
- Add a `--replay manifest.json` command that recreates a run exactly.
- Treat the current result files as provisional until their build provenance is known.

### 4. Revalidate all headline results

The paper calculates that 10 seeds x 200 matches x 200 hands equals 2,000,000 hands. It equals **400,000 maximum hands**. The paper and repository must use the same configuration and report actual hands played, especially when matches end early.

After correcting the simulator and protocol:

1. Rebuild the native extension from the canonical source.
2. Run the correctness suite.
3. Run mirror controls and position controls.
4. Rerun all v0/v1/v2 comparisons from a checked-in manifest.
5. Generate tables and figures directly from raw results.
6. Replace the paper's headline numbers only with regenerated output.

## Codebase cleanup plan

### Establish one canonical project tree

The untracked `headsuptexashva/` directory is a second, non-identical copy of the project. It contains 91 files and makes it unclear which source is authoritative.

Required change:

- Compare it against the root project and preserve only intentional work.
- Use the repository root as the canonical source tree.
- Move any unique material into the root with reviewed commits.
- Archive or remove the duplicate only after verifying it is no longer needed.

Do not delete it blindly: it is untracked and may contain work not present in the root.

### Proposed target structure

```text
heads-up-poker/
  src/
    poker_engine/          # C++ rules, evaluator, simulation core
    poker_ai/              # Python package: bots, policies, evaluation adapters
  apps/
    web/                   # Flask or replacement web demo
  experiments/
    manifests/             # Versioned experiment definitions and seed lists
    runs/                  # Ignored generated raw output
    reports/               # Curated, versioned reviewed summaries only
  tests/
    unit/
    integration/
    properties/
    regression/
  docs/
    game-rules.md
    methodology.md
    reproducibility.md
  paper/
  pyproject.toml
  CMakeLists.txt
  README.md
```

The exact directory names can vary, but the separation of production code, experiments, generated outputs, tests, documentation, and the web app should remain.

### Make the engine authoritative

Current responsibilities are mixed across C++, Python, and `ui/app.py`.

Required refactor:

- Create explicit domain objects: `GameRules`, `GameState`, `HandState`, `Action`, `PlayerState`, `HandResult`, `ExperimentConfig`, and `ExperimentResult`.
- Keep game rules, card dealing, legal actions, betting transitions, pot settlement, and showdown in one engine layer.
- Expose a clean state/action API to Python and the UI.
- Make bot inputs explicit: hole cards, public board, legal action set, pot, to-call amount, stack, street, position, and opponent history.
- Remove duplicated showdown and settlement paths from the web UI.

### Simplify the bot architecture

Each bot should conform to one documented interface and should be independently testable.

Suggested components:

```text
Bot
  -> FeatureExtractor
  -> EquityEstimator
  -> OpponentModel (optional)
  -> Policy
  -> BetSizer
```

For v2 specifically:

- Name it accurately as a heuristic equity policy until it has a genuine opponent model.
- The current opponent action-rate fields are initialized but not learned or used; either implement online range/action updates or remove this feature claim.
- Pass actual position into the bot. `can_check` is not a valid substitute for acting last.
- Make `initial_stack`, margins, rollout count, sizing menu, and board-texture logic explicit configuration values.
- Separate equity estimation from the decision policy and bet sizing.
- Benchmark equity error and runtime separately from match outcomes.

For v3/CFR:

- Do not present it as a mature CFR implementation yet.
- First verify convergence on Kuhn Poker and Leduc Poker against known reference values.
- Use genuine card bucketing and a fixed action abstraction before revisiting Hold'em.
- Track average strategy, iteration count, exploitability proxy, checkpoints, and deterministic training seeds.

## Testing strategy

There is currently no structured automated test suite or CI workflow. The existing `experiments/test_cpp_v2_bot.py` is an experiment runner, not a test suite.

### Unit tests

- Card parsing and formatting for all 52 cards, invalid inputs, and duplicate-card rejection.
- Hand evaluator tests using known five-, six-, and seven-card fixtures.
- Correct ranking order for all hand classes and tie breakers.
- Legal action tests for check, call, fold, bet, raise, cap reached, and insufficient stack.
- Bot tests asserting each bot always returns a legal action and valid bet size.
- Fixed-seed bot determinism tests.

### Property-based tests

Use a property-testing tool such as Hypothesis for Python and randomized C++ tests.

- Every hand has nine unique dealt cards.
- Total chips are conserved after every hand and match.
- No stack, pot, contribution, or to-call value is negative.
- A player never calls or raises more than their stack.
- Every accepted action produces a valid next state.
- Terminal states distribute the complete pot exactly once.
- Replaying the same seed and configuration yields byte-identical raw results.

### Integration and contract tests

- Scripted hands that verify preflop and postflop action order.
- Fold, check-check, bet-call, raise-call, cap-reached, tie, and all-in scenarios.
- UI/API actions replaying the exact same engine transitions as command-line simulations.
- Native module import and a smoke simulation in a clean environment.
- Experiment manifest replay tests, including seed and metadata persistence.

### Statistical validation tests

- v0 versus v0 must be symmetric over a predeclared seed set.
- v1 versus v1 and v2 versus v2 must satisfy a predeclared seat-symmetry tolerance.
- Bot A/B label swaps should produce equivalent outcomes over paired decks.
- Report the statistical unit clearly: match, hand, or paired match.
- Use confidence intervals appropriate to the design; document treatment of ties and any dependence between observations.

### Tooling and CI

- Python: `pytest`, `hypothesis`, `ruff`, `black` or `ruff format`, `mypy` or `pyright`.
- C++: strict warnings, `clang-tidy`, formatted code, sanitizer-enabled debug builds where supported.
- CI: test on Windows and Linux, build the native module, run unit/integration tests, and upload test artifacts.
- Run the fast suite on every pull request; run extended simulation checks on scheduled/manual workflows.

## Build, dependency, and release hygiene

### Packaging

- Add a root `pyproject.toml` defining supported Python versions, runtime dependencies, test dependencies, and development commands.
- Pin or lock all dependencies, including Flask, NumPy, and `pybind11`.
- Document compiler and CMake requirements on Windows and Linux.
- Prefer one documented CMake build path. Keep `build_simple.py` only as a clearly marked fallback if it remains necessary.
- Add a clean-environment smoke test that imports the built extension and runs a tiny deterministic match.

### README

Create a root `README.md` with:

1. Project scope and non-financial disclaimer.
2. Architecture diagram and directory overview.
3. Exact quick-start and build instructions.
4. Test commands and expected outputs.
5. How to reproduce a benchmark from an experiment manifest.
6. Explanation of v0/v1/v2/v3 and current limitations.
7. Links to methodology, results, and citation information.
8. A statement that external results are valid only for the documented simplified game.

### Git hygiene

The existing `.gitignore` is a useful start but needs a deliberate artifact policy.

- Keep source, test fixtures, manifests, documentation, and a small number of reviewed report artifacts under version control.
- Ignore `experiments/runs/`, raw hand logs, large CSV files, transient JSON summaries, coverage, native modules, build trees, local environments, and editor files.
- Use a separate artifact location or release attachment for large reproducible result sets.
- Add `.gitattributes` for consistent line endings and binary-file treatment.
- Remove `cpp_engine/src/simulator.cpp.backup` after confirming it has no unique value.
- Add `LICENSE`, `SECURITY.md`, `CONTRIBUTING.md`, a pull-request template, and optionally `CODEOWNERS`.
- Use professional, descriptive commits such as `fix(engine): deal all cards from one deck` rather than informal history messages.
- Do not rewrite public history solely for appearance; improve all new commits and documentation.

## Web-demo hardening

The current Flask app is useful for local demonstration only.

- Disable Flask debug mode outside local development; never expose the debugger on `0.0.0.0`.
- Replace global match variables with per-session/game storage.
- Validate request bodies and numeric bet sizes; reject malformed input with clear errors.
- Add API tests and structured logging.
- Add a visible label: `Research demo - simplified poker rules - not a production game`.
- If externally hosted, add authentication, rate limiting, secure session management, a production WSGI server, and deployment configuration.

## Paper and PDF improvement plan

The paper should be regenerated only after the correctness work and experiment reruns are complete.

### Required factual corrections

- Correct the hand-count arithmetic and report actual completed hands.
- Align game rules, raise-cap scope, postflop action order, and blind sizes with the final engine.
- Replace time-derived seed claims with the actual manifest/replay mechanism.
- Remove or implement claims around learned opponent modelling and true position-aware behaviour.
- Verify authorship, supervisor, project title, and all metadata on the title page.
- State the exact engine commit and experiment artifact identifiers used for every table and figure.

### Methodology improvements

- Add a formal game definition and state-transition diagram.
- Explain the experimental unit, seed schedule, seat-swapping method, stopping conditions, and treatment of ties.
- Distinguish match win rate, hand win rate, chip EV/profit per hand, and compute cost.
- Add statistical assumptions, limitations, and reasons that Wilson intervals are appropriate for the chosen unit.
- Include a reproducibility appendix with commands and artifact hashes.
- Describe the simplified two-round game as an abstraction, not full heads-up no-limit Hold'em.

### Results improvements

- Generate tables and figures directly from versioned raw data, never manually transcribe values.
- Include number of matches, actual hands, seed count, effect size, uncertainty interval, and wall-clock resources for every comparison.
- Show mirror controls, seat controls, and sensitivity analysis across rollout counts and bot parameters.
- Report negative results and failure analysis for MCCFR without implying that CFR itself is ineffective.
- Avoid phrases such as "essentially perfect" unless they are tightly qualified to the exact simplified benchmark.

### Presentation improvements

- Use a concise executive summary with scope, result, limitation, and reproducibility status.
- Improve the results table so labels do not wrap ambiguously and units are consistent.
- Add a simple architecture figure and evaluation-pipeline figure.
- Keep terminology consistent: `heads-up`, `postflop`, `Monte Carlo`, `MCCFR`, `win rate`, and `profit per hand`.
- Use a professional bibliography style and verify each reference.

## External package for hedge-fund conversations

Prepare this only after the above tests and reruns succeed.

### Recommended deliverables

- An 8-slide presentation: problem, simplified environment, architecture, controls, validation, verified results, limitations, roadmap.
- A short technical whitepaper with reproducibility appendix.
- A private diligence package containing the source snapshot, test report, locked environment, experiment manifests, raw-result hashes, and regenerated figures.
- A concise README that lets a reviewer build, test, and replay a benchmark within minutes.

### What to emphasize

- Engineering discipline: deterministic experiments, native/Python boundary, benchmarking, testing, and audit trail.
- Research judgment: narrow claims, meaningful controls, negative results, and transparent trade-offs.
- Adaptability: clear next steps toward richer simulation and decision policies.

### What not to claim

- That the bot is production poker software.
- That this demonstrates market prediction or financial alpha.
- That MCCFR is validated for full Hold'em.
- That historical results are final until the engine and protocol have been corrected and rerun.

## Implementation sequence

1. Preserve uncommitted work and decide the canonical project tree.
2. Write `docs/game-rules.md` and an experiment-manifest format.
3. Fix the single-deck deal and game-rule discrepancies.
4. Add the rules, property, and native-module smoke tests.
5. Add packaging, lockfile, CI, README, and artifact policy.
6. Refactor UI and bots around the engine contract.
7. Rebuild in a clean environment and rerun verified experiments.
8. Generate the revised paper, technical appendix, and external presentation from those verified artifacts.

## Definition of ready for external review

The project is ready to share when all of the following are true:

- The engine passes deterministic correctness, accounting, and card-uniqueness tests.
- A clean checkout builds the native module and runs the test suite with documented commands.
- Every reported result can be replayed from a manifest with matching metadata and hashes.
- The paper exactly matches the implemented rules and regenerated data.
- The repository has one canonical source tree, a clear README, and no accidental generated artifacts.
- The external narrative accurately presents this as a rigorously engineered research project with limited domain claims.
