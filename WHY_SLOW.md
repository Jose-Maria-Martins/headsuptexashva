# Why V2 Testing is Slower Now

## Test Configuration in run_paper_experiments.py:

```python
'matches': 200,
'hands': 200,
'seeds': 10,
'rollouts': 200
```

## Math:
- **Total matches**: 200 × 10 seeds = 2,000 matches
- **Total hands**: 2,000 × 200 = 400,000 hands
- **Speed**: ~1,000 hands/sec
- **Expected time**: 400,000 / 1,000 = **400 seconds = ~6.7 minutes**

## Why It Feels Slower:

### Before (Estimated):
- Lower rollouts (?)
- Maybe fewer seeds
- Faster hand decisions

### Now:
- Full 400,000 hands per experiment
- Comprehensive statistics
- Multiple experiments (6 total)

### Total Time for ALL Experiments:
- V1 vs V0: ~30 seconds (no Monte Carlo)
- V2 vs V0: ~7 minutes (200 rollouts)
- V2 vs V1: ~7 minutes (both bots need decisions)
- V2 vs V2: ~7 minutes
- V1 vs V1: ~30 seconds
- V0 vs V0: ~30 seconds

**TOTAL**: ~25-30 minutes for complete paper experiments

## Solutions:

### Option 1: Reduce for Testing
```python
'matches': 50,    # was 200
'hands': 100,    # was 200  
'seeds': 3,      # was 10
'rollouts': 100   # was 200
```
**Time**: ~3-4 minutes total (30x faster!)

### Option 2: Keep for Paper
Keep current settings for publication-quality results.

### Option 3: Parallel Execution
Run experiments in parallel (requires script modification).

## Status:
- **Nothing is broken**
- **V2 is working correctly**
- **Performance is normal**
- Just takes time for statistical significance!



