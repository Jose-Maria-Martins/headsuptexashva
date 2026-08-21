# Code hierarchy and standards

## Repository hierarchy

The repository has one canonical source tree:

~~~text
cpp_engine/       authoritative rules, dealing, betting, settlement, evaluator
poker_ai/         Python package: bot policies, CFR trainer, abstractions
ui/               local Flask demonstration only
experiments/      manifests and runners; generated runs stay ignored
tests/             unit, integration, property, and regression tests
docs/              game rules, reproducibility, and engineering notes
~~~

The dependency direction should remain one-way:

~~~text
cpp_engine <- poker_ai <- experiments
cpp_engine <- ui
tests -> all production layers
~~~

The UI and experiment runners may call the engine and bot interfaces, but
they must not reimplement pot settlement, card dealing, or legal-action rules.

## Adding a bot

Start from bot-template.py. A bot must expose:

- get_action(hole_cards, board, pot, to_call, stack, can_check)
- get_bet_size(pot, stack)
- deterministic seeding when randomness is used
- a short explanation of its assumptions and limitations

Add the implementation under poker_ai/bots/, export it from
poker_ai/bots/__init__.py, add it to the UI only if it is demonstrable, and
add tests for legal actions, bounded bet sizes, and seeded repeatability.

## Python standards

- Format and lint new code with Ruff (ruff check and ruff format).
- Use type hints for public interfaces.
- Keep policy, state extraction, and bet sizing separate when practical.
- Avoid hidden global state and wall-clock seeds.
- Prefer small functions with one responsibility.
- Use clear names; do not encode version history in variable names.

## C++ standards

- Keep rules and accounting in the engine, not in Python wrappers.
- Build with warnings enabled and treat new warnings as defects.
- Use RAII and standard containers; avoid raw ownership.
- Validate public inputs and raise explicit exceptions for unsupported cases.
- Add a regression test for every rules or settlement change.

## Experiment standards

- Every run starts from a checked-in manifest or explicit seed list.
- Save the commit, seeds, actual hands, configuration, and uncertainty interval.
- Report mirror controls and seat-swapped controls.
- Generated CSV/JSON outputs belong in experiments/runs/ or an external
  artifact store, not in normal source commits.
