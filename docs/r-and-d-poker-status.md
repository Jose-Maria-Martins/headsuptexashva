# R&D Poker PDF status

The accompanying [R&D Poker PDF](r-and-d-poker.pdf) is preserved as the
original project artifact. It is included for context, not as the final
validated research report.

## Why the original results are provisional

The original report predates the current correctness work. In particular,
the simulator's card dealing, betting/pot accounting, action-order rules,
seed handling, and reported hand-count arithmetic were not yet aligned with
the reproducible protocol now documented in this repository.

The current code has a passing correctness suite and deterministic manifests,
but the report has not yet been regenerated from a complete benchmark run.
Until that happens, historical tables and claims in the PDF should not be
treated as final performance evidence.

The planned replacement is a regenerated report whose tables and figures are
created directly from versioned experiment outputs, with the engine commit,
seed manifest, actual hands played, uncertainty intervals, and limitations
shown for every comparison.
