# Current benchmark status

These results were generated locally after the v2 preflop calibration change.
Configuration: 10 deterministic seeds (1001-1010), 20 matches per seed, 100
hands per match, 100 Monte Carlo rollouts, stack 1,000, blinds 10/20. Matches
can end early when a stack reaches zero, so actual hands are reported.

| Comparison | A match wins | 95% interval | Actual hands |
|---|---:|---:|---:|
| Random vs Random | 46.5% | 39.7%-53.4% | 19,912 |
| HandStrength vs HandStrength | 46.0% | 39.2%-52.9% | 14,158 |
| Monte Carlo vs Monte Carlo | 49.0% | 42.2%-55.9% | 19,599 |
| HandStrength vs Random | 97.5% | 94.3%-98.9% | 15,289 |
| Random vs HandStrength | 3.0% | 1.4%-6.4% | 15,730 |
| Monte Carlo vs Random | 97.0% | 93.6%-98.6% | 17,728 |
| Random vs Monte Carlo | 3.5% | 1.7%-7.1% | 18,218 |
| Monte Carlo vs HandStrength | 72.5% | 65.9%-78.2% | 16,906 |
| HandStrength vs Monte Carlo | 23.0% | 17.7%-29.3% | 16,893 |
| Monte Carlo vs MCCFR | 98.0% | 95.0%-99.2% | 14,133 |
| MCCFR vs Monte Carlo | 3.5% | 1.7%-7.1% | 14,394 |

The self-play controls are close to 50%, while role-swapped comparisons
reverse as expected. The v2 action rate after calibration was about 47% in
the v2-v0 run, down from roughly 92% in the earlier uncalibrated smoke run.
The v2-v3 result is still a result for this simplified game, not a claim about
full Hold'em or financial applications.

## Toy-game CFR check

The exploratory Kuhn/Leduc harness can be run with:

~~~text
python experiments/validate_toy_cfr.py --iterations 100000
~~~

At 100,000 iterations it reported mean cumulative-regret-per-iteration of
approximately 0.058 for Kuhn and 0.091 for Leduc. This is useful as a
diagnostic, but it is not yet a formal exploitability validation against
reference equilibria. v3 should remain labelled experimental until that
validation is improved.
