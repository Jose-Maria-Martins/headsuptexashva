"""
Example experiment script demonstrating the poker AI framework.

This script runs a basic experiment comparing two random bots and
demonstrates both Python and C++ simulation backends.
"""

import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from poker_ai import check_cpp_engine
from poker_ai.bots import RandomBot
from poker_ai.simulation import simulate_experiment


def run_python_experiment():
    """Run experiment using pure Python simulation."""
    print("\n" + "=" * 60)
    print("PYTHON SIMULATION EXPERIMENT")
    print("=" * 60)
    
    # Create bots
    bot_a = RandomBot(name="RandomBot-A", seed=42)
    bot_b = RandomBot(name="RandomBot-B", seed=123)
    
    # Run experiment
    results = simulate_experiment(
        bot_a=bot_a,
        bot_b=bot_b,
        num_matches=10,
        hands_per_match=100,
        seed=12345,
        show_progress=True
    )
    
    # Print results
    print("\n📊 RESULTS:")
    print(f"  Total hands: {results['experiment_config']['total_hands']}")
    print(f"  {bot_a.name} win rate: {results['summary']['bot_a_win_rate']:.2%}")
    print(f"  {bot_b.name} win rate: {results['summary']['bot_b_win_rate']:.2%}")
    print(f"  Time elapsed: {results['summary']['elapsed_time_seconds']:.2f}s")
    print(f"  Hands/second: {results['summary']['hands_per_second']:.0f}")
    
    return results


def run_cpp_experiment():
    """Run experiment using C++ simulation backend."""
    print("\n" + "=" * 60)
    print("C++ SIMULATION EXPERIMENT")
    print("=" * 60)
    
    try:
        from poker_ai import poker_engine
        import time
        
        # Create configuration
        config = poker_engine.SimConfig()
        config.initial_stack = 1000
        config.small_blind = 5
        config.big_blind = 10
        config.seed = 12345
        
        # Create simulator and bots
        sim = poker_engine.Simulator(config)
        bot_a = poker_engine.RandomBot(42)
        bot_b = poker_engine.RandomBot(123)
        
        print("\n🚀 Running 10 matches of 100 hands each...")
        
        # Time the C++ simulation
        start_time = time.time()
        results = sim.simulate_batch(bot_a, bot_b, num_matches=10, hands_per_match=100)
        end_time = time.time()
        
        # Calculate performance
        elapsed = end_time - start_time
        total_hands = sum(r.hands_played for r in results)
        hands_per_second = total_hands / elapsed if elapsed > 0 else 0
        
        # Aggregate results
        total_p0_wins = sum(r.p0_wins for r in results)
        total_p1_wins = sum(r.p1_wins for r in results)
        
        print("\n📊 RESULTS:")
        print(f"  Total hands: {total_hands}")
        print(f"  Bot A win rate: {total_p0_wins / total_hands:.2%}")
        print(f"  Bot B win rate: {total_p1_wins / total_hands:.2%}")
        print(f"  Time elapsed: {elapsed:.3f}s")
        print(f"  Hands/second: {hands_per_second:,.0f}")
        print(f"  ⚡ C++ backend - {hands_per_second/1000:.1f}k hands/sec!")
        
        return results
        
    except ImportError:
        print("\n⚠️  C++ engine not available.")
        print("Build it with:")
        print("  mkdir build && cd build")
        print("  cmake ..")
        print("  cmake --build . --config Release")
        return None


def test_hand_evaluation():
    """Test hand evaluation with C++ backend."""
    print("\n" + "=" * 60)
    print("HAND EVALUATION TEST")
    print("=" * 60)
    
    try:
        from poker_ai import poker_engine
        
        # Test some hands
        test_hands = [
            (["As", "Ah", "Ad", "Ac", "Ks", "Kh", "Kd"], "Four of a Kind"),
            (["As", "Ks", "Qs", "Js", "Ts", "9h", "8h"], "Straight Flush"),
            (["Ah", "Kh", "Qh", "Jh", "9h", "2c", "3d"], "Flush"),
            (["Ac", "Ad", "Kc", "Kd", "Qc", "2h", "3s"], "Two Pair"),
        ]
        
        print("\nEvaluating hands:")
        for cards, expected in test_hands:
            score, description = poker_engine.evaluate_hand_string(cards)
            print(f"  {' '.join(cards):40} → {description} (score: {score})")
        
    except ImportError:
        print("C++ engine not available - skipping hand evaluation test")


def main():
    """Run all experiments."""
    print("\n" + "=" * 60)
    print("🎯 HEADS-UP POKER AI RESEARCH PLATFORM")
    print("=" * 60)
    print("\nVersion: 0.1.0")
    print("Purpose: Research-grade poker AI with Monte Carlo and CFR")
    
    # Check C++ engine availability
    print("\n" + "-" * 60)
    check_cpp_engine()
    print("-" * 60)
    
    # Run experiments
    python_results = run_python_experiment()
    cpp_results = run_cpp_experiment()
    
    # Test hand evaluation
    test_hand_evaluation()
    
    print("\n" + "=" * 60)
    print("✅ EXPERIMENT COMPLETE")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Implement rule-based bot (v1)")
    print("  2. Add Monte Carlo equity calculations")
    print("  3. Implement CFR algorithm (v3)")
    print("  4. Run large-scale experiments (100k+ hands)")
    print("  5. Generate analysis and visualizations")
    print("  6. Write research paper")
    
    # Save results in both JSON and CSV
    output_dir = Path(__file__).parent
    
    # Save JSON (for detailed analysis)
    json_file = output_dir / "results.json"
    with open(json_file, "w") as f:
        json.dump(python_results, f, indent=2)
    
    # Save CSV (for spreadsheet analysis)
    csv_file = output_dir / "results.csv"
    import pandas as pd
    
    # Convert to DataFrame
    match_data = []
    for i, match in enumerate(python_results['match_results']):
        match_data.append({
            'match_id': i + 1,
            'hands_played': match['hands_played'],
            'bot_a_wins': match['bot_a_wins'],
            'bot_b_wins': match['bot_b_wins'],
            'bot_a_win_rate': match['bot_a_win_rate'],
            'bot_b_win_rate': match['bot_b_win_rate'],
            'bot_a_final_stack': match['bot_a_final_stack'],
            'bot_b_final_stack': match['bot_b_final_stack']
        })
    
    df = pd.DataFrame(match_data)
    df.to_csv(csv_file, index=False)
    
    print(f"\n📁 Results saved to:")
    print(f"  📄 JSON: {json_file}")
    print(f"  📊 CSV:  {csv_file}")


if __name__ == "__main__":
    main()

