#!/usr/bin/env python3
"""
Paper Experiments for V1 and V2 Bots
Comprehensive testing for research paper with statistical significance.
"""

import subprocess
import sys
import time
import json
from pathlib import Path


def run_experiment(bot_a, bot_b, matches=200, hands=200, seeds=10, rollouts=300, 
                  description=""):
    """Run a single experiment and return the results."""
    print(f"\n{'='*80}")
    print(f"PAPER EXPERIMENT: {description}")
    print(f"Configuration: {bot_a.upper()} vs {bot_b.upper()}")
    print(f"Parameters: {matches} matches, {hands} hands, {seeds} seeds")
    if bot_a == "montecarlo" or bot_b == "montecarlo":
        print(f"Monte Carlo rollouts: {rollouts}")
    print(f"{'='*80}")
    
    cmd = [
        sys.executable, "experiments/test_cpp_v2_bot.py",
        "--botA", bot_a,
        "--botB", bot_b,
        "--matches", str(matches),
        "--hands", str(hands),
        "--seeds", str(seeds),
        "--rollouts", str(rollouts)
    ]
    
    start_time = time.time()
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path(__file__).parent)
        elapsed = time.time() - start_time
        
        if result.returncode == 0:
            # Find the JSON file from the output
            output_lines = result.stdout.split('\n')
            json_path = None
            for line in output_lines:
                if 'JSON:' in line:
                    json_path = line.split('JSON:')[1].strip()
                    break
            
            if json_path and Path(json_path).exists():
                try:
                    with open(json_path, 'r') as f:
                        data = json.load(f)
                    
                    results = {
                        'description': description,
                        'bot_a': bot_a,
                        'bot_b': bot_b,
                        'config': data['config'],
                        'results': data['results'],
                        'elapsed': elapsed,
                        'success': True
                    }
                    
                    # Print key results
                    win_rate = data['results']['match_win_rate_A']
                    ci_low = data['results']['match_win_rate_A_CI95'][0]
                    ci_high = data['results']['match_win_rate_A_CI95'][1]
                    stack_diff = data['results']['stack_diff']
                    hands_per_sec = data['results']['hands_per_second']
                    
                    print(f"RESULTS:")
                    print(f"  Win Rate A: {win_rate*100:.1f}% (95% CI: [{ci_low*100:.1f}%, {ci_high*100:.1f}%])")
                    print(f"  Stack Difference: {stack_diff:+.0f}")
                    print(f"  Performance: {hands_per_sec:,.0f} hands/sec")
                    print(f"  Total Time: {elapsed:.1f}s")
                    
                    return results
                except Exception as e:
                    print(f"Error reading JSON: {e}")
            
            print("SUCCESS (couldn't parse results)")
            return {'success': False, 'elapsed': elapsed, 'error': 'JSON parsing failed'}
        else:
            print(f"ERROR: {result.stderr}")
            return {'success': False, 'elapsed': elapsed, 'error': result.stderr}
    except Exception as e:
        print(f"EXCEPTION: {e}")
        return {'success': False, 'elapsed': time.time() - start_time, 'error': str(e)}


def main():
    print("PAPER EXPERIMENTS - V1 AND V2 BOT EVALUATION")
    print("=" * 80)
    print("Statistical significance: 200 games, 200 hands, 10 seeds")
    print("Total hands per experiment: 400,000")
    print("=" * 80)
    
    # Paper experiments with statistical significance
    experiments = [
        # V1 vs V0 (Baseline)
        {
            'bot_a': 'handstrength',
            'bot_b': 'random',
            'matches': 200,
            'hands': 200,
            'seeds': 10,
            'rollouts': 0,
            'description': 'V1 (HandStrength) vs V0 (Random) - Baseline Performance'
        },
        
        # V2 vs V0 (Main comparison)
        {
            'bot_a': 'montecarlo',
            'bot_b': 'random',
            'matches': 200,
            'hands': 200,
            'seeds': 10,
            'rollouts': 200,  # Reduced for speed
            'description': 'V2 (MonteCarlo) vs V0 (Random) - Main Performance Test'
        },
        
        # V2 vs V1 (Direct comparison)
        {
            'bot_a': 'montecarlo',
            'bot_b': 'handstrength',
            'matches': 200,
            'hands': 200,
            'seeds': 10,
            'rollouts': 200,
            'description': 'V2 (MonteCarlo) vs V1 (HandStrength) - Direct Comparison'
        },
        
        # V2 vs V2 (Position bias test)
        {
            'bot_a': 'montecarlo',
            'bot_b': 'montecarlo',
            'matches': 200,
            'hands': 200,
            'seeds': 10,
            'rollouts': 200,
            'description': 'V2 (MonteCarlo) vs V2 (MonteCarlo) - Position Bias Test'
        },
        
        # V1 vs V1 (V1 position bias test)
        {
            'bot_a': 'handstrength',
            'bot_b': 'handstrength',
            'matches': 200,
            'hands': 200,
            'seeds': 10,
            'rollouts': 0,
            'description': 'V1 (HandStrength) vs V1 (HandStrength) - V1 Position Bias Test'
        },
        
        # Random vs Random (Control)
        {
            'bot_a': 'random',
            'bot_b': 'random',
            'matches': 200,
            'hands': 200,
            'seeds': 10,
            'rollouts': 0,
            'description': 'V0 (Random) vs V0 (Random) - Control Group'
        }
    ]
    
    results = []
    total_time = 0
    
    for i, exp in enumerate(experiments, 1):
        print(f"\n[{i}/{len(experiments)}] {exp['description']}")
        
        result = run_experiment(
            exp['bot_a'], exp['bot_b'], 
            exp['matches'], exp['hands'], exp['seeds'], exp['rollouts'],
            exp['description']
        )
        
        results.append(result)
        total_time += result['elapsed']
        
        if result['success']:
            print(f"[OK] Completed in {result['elapsed']:.1f}s")
        else:
            print(f"[FAIL] Failed after {result['elapsed']:.1f}s: {result.get('error', 'Unknown error')}")
    
    # Summary
    print(f"\n{'='*100}")
    print("PAPER EXPERIMENTS SUMMARY")
    print(f"{'='*100}")
    
    successful = sum(1 for r in results if r['success'])
    failed = len(results) - successful
    
    print(f"Total experiments: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Total time: {total_time:.1f}s ({total_time/60:.1f} minutes)")
    print(f"Average time per experiment: {total_time/len(results):.1f}s")
    
    # Results table
    print(f"\n{'='*120}")
    print("DETAILED RESULTS TABLE")
    print(f"{'='*120}")
    print(f"{'Experiment':<50} {'Win Rate A':<12} {'95% CI':<20} {'Stack Diff':<12} {'Hands/sec':<12} {'Time':<8}")
    print(f"{'-'*120}")
    
    for r in results:
        if r['success']:
            win_rate = r['results']['match_win_rate_A']
            ci_low = r['results']['match_win_rate_A_CI95'][0]
            ci_high = r['results']['match_win_rate_A_CI95'][1]
            stack_diff = r['results']['stack_diff']
            hands_per_sec = r['results']['hands_per_second']
            
            print(f"{r['description']:<50} {win_rate*100:>8.1f}% {f'[{ci_low*100:.1f}%, {ci_high*100:.1f}%]':<20} {stack_diff:>+10.0f} {hands_per_sec:>10,.0f} {r['elapsed']:>6.1f}s")
        else:
            print(f"{r['description']:<50} {'FAIL':<12} {'N/A':<20} {'N/A':<12} {'N/A':<12} {r['elapsed']:>6.1f}s")
    
    # Performance analysis
    print(f"\n{'='*80}")
    print("PERFORMANCE ANALYSIS")
    print(f"{'='*80}")
    
    v1_vs_random = next((r for r in results if r['success'] and r['description'].startswith('V1 (HandStrength) vs V0 (Random)')), None)
    v2_vs_random = next((r for r in results if r['success'] and r['description'].startswith('V2 (MonteCarlo) vs V0 (Random)')), None)
    v2_vs_v1 = next((r for r in results if r['success'] and r['description'].startswith('V2 (MonteCarlo) vs V1 (HandStrength)')), None)
    
    if v1_vs_random and v2_vs_random:
        v1_win_rate = v1_vs_random['results']['match_win_rate_A']
        v2_win_rate = v2_vs_random['results']['match_win_rate_A']
        improvement = v2_win_rate - v1_win_rate
        print(f"V1 vs Random: {v1_win_rate*100:.1f}% win rate")
        print(f"V2 vs Random: {v2_win_rate*100:.1f}% win rate")
        print(f"V2 improvement over V1: {improvement*100:+.1f} percentage points")
    
    if v2_vs_v1:
        v2_vs_v1_rate = v2_vs_v1['results']['match_win_rate_A']
        print(f"V2 vs V1: {v2_vs_v1_rate*100:.1f}% win rate for V2")
    
    # Position bias analysis
    v2_vs_v2 = next((r for r in results if r['success'] and r['description'].startswith('V2 (MonteCarlo) vs V2 (MonteCarlo)')), None)
    v1_vs_v1 = next((r for r in results if r['success'] and r['description'].startswith('V1 (HandStrength) vs V1 (HandStrength)')), None)
    
    if v2_vs_v2:
        v2_bias = abs(v2_vs_v2['results']['match_win_rate_A'] - 0.5)
        print(f"V2 position bias: {v2_bias*100:.1f}% (should be close to 0%)")
    
    if v1_vs_v1:
        v1_bias = abs(v1_vs_v1['results']['match_win_rate_A'] - 0.5)
        print(f"V1 position bias: {v1_bias*100:.1f}% (should be close to 0%)")
    
    print(f"\n{'='*80}")
    print("EXPERIMENTS COMPLETE - READY FOR PAPER")
    print(f"{'='*80}")
    print("All results saved to 'experiments/' directory")
    print("Use these results for the research paper methodology and results sections")


if __name__ == "__main__":
    main()
