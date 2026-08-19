# Comparison: `headsuptexashva/` vs repository root

The untracked `headsuptexashva/` directory is a nested copy of the project (including its own `.git` metadata). **The repository root is canonical.** Do not delete the duplicate until any unique work is merged.

## Summary (2026-08-19)

| Category | Status |
|----------|--------|
| C++ engine core (`hand_evaluator`, `poker_engine`, `bindings`) | Identical between copies |
| `cpp_engine/src/simulator.cpp` | **Differs** — both copies share the separate-deck bug; neither has the fix yet |
| `cpp_engine/src/simulator.cpp.backup` | Present only in duplicate (no unique logic; safe to ignore) |
| Python bots (`poker_ai/bots/*`) | **Differs** — root has user uncommitted edits to `random_bot.py` |
| CFR trainer / abstraction | **Differs** — minor divergence; root is authoritative |
| UI (`ui/*`) | **Differs** — root has user uncommitted edits to `app.py`, `play.html`, `style.css` |
| Experiments | Duplicate contains overlapping JSON summaries; root also has newer summaries |
| `run_paper_experiments.py` | **Differs** |

## Recommendation

1. Treat **root** as the single source tree going forward.
2. Do **not** merge duplicate UI/bot changes blindly — root already has active user work.
3. Apply engine correctness fixes only under root `cpp_engine/`.
4. After verification, `headsuptexashva/` can be archived or removed manually; no unique engine fixes were found in the duplicate.
