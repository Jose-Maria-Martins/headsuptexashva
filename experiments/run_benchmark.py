"""
Test Monte Carlo Bot (V2) using C++ simulation.
Comprehensive testing of V2 against V1, V0, and itself.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import time
import json
import csv
import math
import argparse
from datetime import datetime

from experiments.manifest_utils import (
    build_provenance,
    default_run_dir,
    load_manifest,
    resolve_seeds,
)


def wilson_ci(p: float, n: int, z: float = 1.96):
    if n == 0:
        return (0.0, 0.0)
    denom = 1.0 + (z * z) / n
    center = (p + (z * z) / (2 * n)) / denom
    margin = (z / denom) * math.sqrt((p * (1 - p) + (z * z) / (4 * n)) / n)
    return (max(0.0, center - margin), min(1.0, center + margin))


def run_single_seed(seed: int, matches: int, hands: int, stack: int, sb: int, bb: int, 
                   bot_a_type: str, bot_b_type: str, rollouts: int = 300, strategy_path: str = "poker_ai/cfr/strategy.json"):
    """Run one seed worth of matches, return (results_list, timing_sec)."""
    try:
        from poker_ai import poker_engine
        from poker_ai.bots.random_bot import RandomBot as PyRandomBot
        from poker_ai.bots.hand_strength_bot import HandStrengthBot as PyHandStrengthBot
        from poker_ai.bots.monte_carlo_bot import MonteCarloBot as PyMonteCarloBot
        from poker_ai.bots.mccfr_bot import MCCFRBot as PyMCCFRBot

        # Wrap Python bot logic in C++ Bot subclass
        class CPPRandomBot(poker_engine.Bot):
            def __init__(self, seed_value: int = 12345):
                super().__init__()
                self._impl = PyRandomBot(seed_value)

            def get_action(self, hole_cards, board, pot, to_call, stack, can_check):
                return self._impl.get_action(hole_cards, board, pot, to_call, stack, can_check)

            def get_bet_size(self, pot, stack):
                return self._impl.get_bet_size(pot, stack)

        class CPPHandStrengthBot(poker_engine.Bot):
            def __init__(self, seed_value: int = 12345):
                super().__init__()
                self._impl = PyHandStrengthBot(seed_value)

            def get_action(self, hole_cards, board, pot, to_call, stack, can_check):
                return self._impl.get_action(hole_cards, board, pot, to_call, stack, can_check)

            def get_bet_size(self, pot, stack):
                return self._impl.get_bet_size(pot, stack)

        class CPPMonteCarloBot(poker_engine.Bot):
            def __init__(self, seed_value: int = 12345, rollouts: int = 300):
                super().__init__()
                self._impl = PyMonteCarloBot(seed_value, rollouts=rollouts)

            def get_action(self, hole_cards, board, pot, to_call, stack, can_check):
                return self._impl.get_action(hole_cards, board, pot, to_call, stack, can_check)

            def get_bet_size(self, pot, stack):
                return self._impl.get_bet_size(pot, stack)
        
        class CPPMCCFRBot(poker_engine.Bot):
            def __init__(self, strategy_path: str, seed_value: int = 12345):
                super().__init__()
                self._impl = PyMCCFRBot(strategy_path=strategy_path, player_id=0, seed=seed_value)
            
            def get_action(self, hole_cards, board, pot, to_call, stack, can_check):
                return self._impl.get_action(hole_cards, board, pot, to_call, stack, can_check)
            
            def get_bet_size(self, pot, stack):
                return self._impl.get_bet_size(pot, stack)

        # Config and simulator
        config = poker_engine.SimConfig()
        config.initial_stack = stack
        config.small_blind = sb
        config.big_blind = bb
        config.seed = seed

        sim = poker_engine.Simulator(config)

        # Create bots based on type
        if bot_a_type == "random":
            bot_a = CPPRandomBot(seed + 7)
        elif bot_a_type == "handstrength":
            bot_a = CPPHandStrengthBot(seed + 7)
        elif bot_a_type == "montecarlo":
            bot_a = CPPMonteCarloBot(seed + 7, rollouts=rollouts)
        elif bot_a_type == "mccfr":
            bot_a = CPPMCCFRBot(strategy_path, seed + 7)
        else:
            raise ValueError(f"Unknown bot type: {bot_a_type}")

        if bot_b_type == "random":
            bot_b = CPPRandomBot(seed + 28)
        elif bot_b_type == "handstrength":
            bot_b = CPPHandStrengthBot(seed + 28)
        elif bot_b_type == "montecarlo":
            bot_b = CPPMonteCarloBot(seed + 28, rollouts=rollouts)
        elif bot_b_type == "mccfr":
            bot_b = CPPMCCFRBot(strategy_path, seed + 28)
        else:
            raise ValueError(f"Unknown bot type: {bot_b_type}")

        start_time = time.time()
        results = sim.simulate_batch(bot_a, bot_b, num_matches=matches, hands_per_match=hands)
        elapsed = time.time() - start_time

        return results, elapsed

    except ImportError as e:
        print(f"[ERROR] C++ engine not available: {e}")
        print("Build it with: python build_simple.py")
        return [], 0.0


def write_csv(path, rows, header):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="C++ V2/V3 Bot experiment runner")
    parser.add_argument("--botA", type=str, default="montecarlo", 
                       choices=["random", "handstrength", "montecarlo", "mccfr"],
                       help="Bot A type")
    parser.add_argument("--botB", type=str, default="handstrength",
                       choices=["random", "handstrength", "montecarlo", "mccfr"], 
                       help="Bot B type")
    parser.add_argument("--strategy-path", type=str, default="poker_ai/cfr/strategy.json",
                       help="Path to MCCFR strategy file")
    parser.add_argument("--matches", type=int, default=100)
    parser.add_argument("--hands", type=int, default=100)
    parser.add_argument("--seeds", type=int, default=10)
    parser.add_argument("--stack", type=int, default=1000)
    parser.add_argument("--sb", type=int, default=10)
    parser.add_argument("--bb", type=int, default=20)
    parser.add_argument("--rollouts", type=int, default=300, help="Monte Carlo rollouts")
    parser.add_argument("--out", type=str, default="experiments/runs")
    parser.add_argument("--manifest", type=str, default=None, help="Experiment manifest JSON")
    parser.add_argument("--replay", type=str, default=None, help="Replay from prior summary/manifest JSON")
    parser.add_argument("--seed-list", type=str, default=None, help="Comma-separated explicit seeds")
    args = parser.parse_args()

    if args.replay:
        replay_data = load_manifest(args.replay)
        cfg = replay_data.get("config", replay_data)
        args.botA = cfg.get("bot_a", args.botA)
        args.botB = cfg.get("bot_b", args.botB)
        args.matches = cfg.get("matches", args.matches)
        args.hands = cfg.get("hands", cfg.get("hands_per_match", args.hands))
        args.stack = cfg.get("stack", args.stack)
        args.sb = cfg.get("small_blind", args.sb)
        args.bb = cfg.get("big_blind", args.bb)
        args.rollouts = cfg.get("rollouts", args.rollouts)
        seed_values = cfg.get("seeds") or resolve_seeds(replay_data)
    elif args.manifest:
        manifest = load_manifest(args.manifest)
        args.botA = manifest.get("bot_a", args.botA)
        args.botB = manifest.get("bot_b", args.botB)
        args.matches = manifest.get("matches", args.matches)
        args.hands = manifest.get("hands_per_match", manifest.get("hands", args.hands))
        args.stack = manifest.get("stack", args.stack)
        args.sb = manifest.get("small_blind", args.sb)
        args.bb = manifest.get("big_blind", args.bb)
        args.rollouts = manifest.get("rollouts", args.rollouts)
        seed_values = resolve_seeds(manifest)
    elif args.seed_list:
        seed_values = [int(s.strip()) for s in args.seed_list.split(",") if s.strip()]
    else:
        # Deterministic default schedule (no wall-clock seeds)
        seed_values = list(range(1001, 1001 + args.seeds))

    print("=" * 80)
    print("C++ SIMULATION - MONTE CARLO BOT (V2) COMPREHENSIVE TESTING")
    print("=" * 80)
    print(f"[CONFIG] matches={args.matches} hands={args.hands} seeds={len(seed_values)} stack={args.stack} sb/bb={args.sb}/{args.bb}")
    print(f"[SEEDS] {seed_values}")
    print(f"[BOTS] {args.botA.upper()} vs {args.botB.upper()}")
    if args.botA == "montecarlo" or args.botB == "montecarlo":
        print(f"[MONTE CARLO] rollouts={args.rollouts}")
    
    expected_hands = args.matches * args.hands * len(seed_values)
    print(f"[ESTIMATE] ~{expected_hands:,} hands total (may finish early if stacks run out)")

    all_rows = []
    # Optional metric accumulators
    p0_action_counts = {"fold": 0, "call": 0, "raise": 0}
    p1_action_counts = {"fold": 0, "call": 0, "raise": 0}
    p0_wins_by_rank = [0]*9
    p1_wins_by_rank = [0]*9
    total_elapsed = 0.0
    total_hands_global = 0

    for s, seed in enumerate(seed_values):
        print(f"\n[SEED {s+1}/{len(seed_values)}] starting with seed={seed}...", flush=True)
        seed_start = time.time()
        
        results, elapsed = run_single_seed(
            seed,
            args.matches,
            args.hands,
            args.stack,
            args.sb,
            args.bb,
            args.botA,
            args.botB,
            args.rollouts,
            args.strategy_path,
        )
        
        total_elapsed += elapsed

        # Aggregate per-seed
        for i, r in enumerate(results):
            total_hands_global += r.hands_played
            all_rows.append([
                seed, i, r.hands_played, r.p0_wins, r.p1_wins, r.ties,
                r.p0_final_stack, r.p1_final_stack, r.match_winner
            ])
            # Accumulate optional metrics if present
            try:
                p0_action_counts["fold"] += getattr(r, "p0_folds", 0)
                p0_action_counts["call"] += getattr(r, "p0_calls", 0)
                p0_action_counts["raise"] += getattr(r, "p0_raises", 0)
                p1_action_counts["fold"] += getattr(r, "p1_folds", 0)
                p1_action_counts["call"] += getattr(r, "p1_calls", 0)
                p1_action_counts["raise"] += getattr(r, "p1_raises", 0)
                p0_wins_by_rank = [a+b for a,b in zip(p0_wins_by_rank, getattr(r, "p0_wins_by_rank", []))]
                p1_wins_by_rank = [a+b for a,b in zip(p1_wins_by_rank, getattr(r, "p1_wins_by_rank", []))]
            except Exception:
                pass

        # Per-seed progress summary
        seed_elapsed = time.time() - seed_start
        seed_hands = sum(r.hands_played for r in results)
        seed_hps = (seed_hands / seed_elapsed) if seed_elapsed > 0 else 0.0
        remaining_seeds = len(seed_values) - (s + 1)
        eta_sec = (seed_elapsed * remaining_seeds)
        print(
            f"[SEED {s+1}/{len(seed_values)}] hands={seed_hands} time={seed_elapsed:.2f}s rate={seed_hps:,.0f} h/s ETA~{eta_sec/60:.1f}m",
            flush=True,
        )

    # Compute metrics
    matches_total = len(all_rows)
    match_wins_p0 = sum(1 for row in all_rows if row[8] == 0)
    match_wins_p1 = sum(1 for row in all_rows if row[8] == 1)
    ties = matches_total - match_wins_p0 - match_wins_p1
    match_win_rate = match_wins_p0 / matches_total if matches_total else 0.0
    ci_low, ci_high = wilson_ci(match_win_rate, matches_total)

    avg_p0_stack = sum(row[6] for row in all_rows) / matches_total if matches_total else 0.0
    avg_p1_stack = sum(row[7] for row in all_rows) / matches_total if matches_total else 0.0
    avg_stack_diff = avg_p0_stack - avg_p1_stack

    # Profit is measured relative to starting stack
    profit_per_match = (avg_p0_stack - args.stack)
    profit_per_hand = (profit_per_match / args.hands) if matches_total else 0.0

    hps = (total_hands_global / total_elapsed) if total_elapsed > 0 else 0.0

    # Print summary
    print("\n[RESULTS]")
    print(f"  Matches: {matches_total}")
    print(f"  Match wins (A): {match_wins_p0} ({match_win_rate:.2%})  95% CI: [{ci_low:.2%}, {ci_high:.2%}]")
    print(f"  Match wins (B): {match_wins_p1} ({match_wins_p1/matches_total:.2%})  Ties: {ties}")
    print(f"  Avg final stack (A): {avg_p0_stack:.1f}  (B): {avg_p1_stack:.1f}  Diff: {avg_stack_diff:.1f}")
    print(f"  Profit per match (A): {profit_per_match:.1f}  Profit per hand (A): {profit_per_hand:.4f}")
    print("\n[PERFORMANCE]")
    print(f"  Total hands: {total_hands_global}")
    print(f"  Total time: {total_elapsed:.3f}s  Hands/sec: {hps:,.0f}")

    # Optional metrics printing
    rank_names = [
        "HIGH_CARD","PAIR","TWO_PAIR","THREE_OF_A_KIND",
        "STRAIGHT","FLUSH","FULL_HOUSE","FOUR_OF_A_KIND","STRAIGHT_FLUSH"
    ]
    actions_total_p0 = sum(p0_action_counts.values()) or 1
    actions_total_p1 = sum(p1_action_counts.values()) or 1
    print("\n[ACTIONS]")
    print(f"  Bot A: fold {p0_action_counts['fold']}, call {p0_action_counts['call']}, raise/bet {p0_action_counts['raise']}")
    print(f"         (% {p0_action_counts['fold']/actions_total_p0:.1%}, {p0_action_counts['call']/actions_total_p0:.1%}, {p0_action_counts['raise']/actions_total_p0:.1%})")
    print(f"  Bot B: fold {p1_action_counts['fold']}, call {p1_action_counts['call']}, raise/bet {p1_action_counts['raise']}")
    print(f"         (% {p1_action_counts['fold']/actions_total_p1:.1%}, {p1_action_counts['call']/actions_total_p1:.1%}, {p1_action_counts['raise']/actions_total_p1:.1%})")

    total_rank_A = sum(p0_wins_by_rank) or 1
    total_rank_B = sum(p1_wins_by_rank) or 1
    print("\n[SHOWDOWN WINS BY HAND RANK]")
    for i, name in enumerate(rank_names):
        a = p0_wins_by_rank[i] if i < len(p0_wins_by_rank) else 0
        b = p1_wins_by_rank[i] if i < len(p1_wins_by_rank) else 0
        print(f"  {name:16s}  A: {a} ({a/total_rank_A:.1%})   B: {b} ({b/total_rank_B:.1%})")

    # Write outputs under experiments/runs/
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_name = f"{args.botA}_vs_{args.botB}_{ts}"
    out_dir = Path(args.out)
    if out_dir.name == "runs" or "runs" in out_dir.parts:
        out_dir = out_dir / run_name
    else:
        out_dir = default_run_dir(f"{args.botA}_vs_{args.botB}")
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "matches.csv"
    json_path = out_dir / "summary.json"
    manifest_copy = out_dir / "manifest_resolved.json"

    write_csv(
        str(csv_path),
        all_rows,
        ["seed", "match_id", "hands_played", "p0_wins", "p1_wins", "ties", "p0_final_stack", "p1_final_stack", "match_winner"]
    )

    summary = {
        "config": {
            "bot_a": args.botA,
            "bot_b": args.botB,
            "matches": args.matches,
            "hands": args.hands,
            "hands_per_match": args.hands,
            "seeds": seed_values,
            "stack": args.stack,
            "small_blind": args.sb,
            "big_blind": args.bb,
            "rollouts": args.rollouts,
        },
        "provenance": build_provenance(
            {
                "name": run_name,
                "bot_a": args.botA,
                "bot_b": args.botB,
                "matches": args.matches,
                "hands_per_match": args.hands,
                "seeds": seed_values,
                "stack": args.stack,
                "small_blind": args.sb,
                "big_blind": args.bb,
                "rollouts": args.rollouts,
            },
            output_paths=[csv_path],
        ),
        "results": {
            "matches": matches_total,
            "match_wins_A": match_wins_p0,
            "match_wins_B": match_wins_p1,
            "match_win_rate_A": match_win_rate,
            "match_win_rate_A_CI95": [ci_low, ci_high],
            "avg_final_stack_A": avg_p0_stack,
            "avg_final_stack_B": avg_p1_stack,
            "stack_diff": avg_stack_diff,
            "profit_per_match_A": profit_per_match,
            "profit_per_hand_A": profit_per_hand,
            "hands_per_second": hps,
            "total_hands": total_hands_global,
            "total_time_sec": total_elapsed,
            "actions_A": p0_action_counts,
            "actions_B": p1_action_counts,
            "wins_by_rank_A": p0_wins_by_rank,
            "wins_by_rank_B": p1_wins_by_rank,
        },
        "artifacts": {
            "csv": str(csv_path),
            "json": str(json_path),
        },
    }

    with open(json_path, "w") as f:
        json.dump(summary, f, indent=2)

    resolved_manifest = summary["config"].copy()
    resolved_manifest["schema_version"] = 1
    resolved_manifest["name"] = run_name
    with open(manifest_copy, "w") as f:
        json.dump(resolved_manifest, f, indent=2)

    print("\n[SAVED]")
    print(f"  CSV:  {csv_path}")
    print(f"  JSON: {json_path}")

