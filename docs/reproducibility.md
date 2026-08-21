# Reproducibility

## Principles

1. **Explicit seeds** — never derive seeds from wall-clock time in committed workflows.
2. **Manifests** — versioned JSON under `experiments/manifests/` defines bot matchups, stack/blinds, and seed lists.
3. **Provenance** — each run records Git commit, dirty flag, Python/platform metadata, and output file hashes.
4. **Ignored raw output** — full CSV/JSON runs live in `experiments/runs/` (not committed). Only reviewed summaries may be curated under `experiments/reports/` when regenerated.

## Manifest format (schema v1)

```json
{
  "schema_version": 1,
  "name": "experiment_id",
  "bot_a": "montecarlo",
  "bot_b": "random",
  "matches": 100,
  "hands_per_match": 200,
  "seeds": [1001, 1002, 1003],
  "stack": 1000,
  "small_blind": 10,
  "big_blind": 20,
  "rollouts": 300
}
```

Alternatively, `"seed_list_file": "experiments/manifests/seeds.txt"` may reference one seed per line.

## Commands

Run from manifest:

```bash
python experiments/run_benchmark.py --manifest experiments/manifests/v2_vs_v0_baseline.json
```

Explicit seed list (CLI override):

```bash
python experiments/run_benchmark.py --seed-list 42,43,44 --matches 10 --hands 50
```

Replay prior run:

```bash
python experiments/run_benchmark.py --replay experiments/runs/<run>/summary.json
```

## Hand-count arithmetic

Maximum dealt hands for a configuration:

```
max_hands = len(seeds) × matches × hands_per_match
```

Actual hands may be lower when stacks bust out before the hand limit. Summaries report `total_hands` from the engine.

## Historical artifacts

JSON summaries in `experiments/v2_summary_*.json` predate manifest/provenance support and may have been produced with:

- separate hole/board decks (invalid duplicates possible);
- wall-clock-derived seeds;
- uncorrected action-order or all-in accounting.

Treat them as **provisional** until replaced by manifest-driven reruns.
