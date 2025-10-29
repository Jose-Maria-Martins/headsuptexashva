# Blind Rotation Fix - Negative Stack Bug

## Problem Found:

The C++ engine was hardcoding blind positions:
```cpp
int sb = 0;  // ALWAYS position 0
int bb = 1;  // ALWAYS position 1
```

This caused **stacks to go negative** because:
1. Blinds were posted to the same array positions every hand
2. No protection against posting more than available chips
3. Pot was calculated from config, not actual blind amounts

## Fix Applied:

### File: `cpp_engine/src/simulator.cpp` (lines 157-175)

**Before:**
```cpp
// Post blinds
int sb = 0;  // Small blind = position 0 (acts first)
int bb = 1;  // Big blind = position 1 (acts second)

stacks[sb] -= config_.small_blind;
stacks[bb] -= config_.big_blind;

int pot = config_.small_blind + config_.big_blind;
```

**After:**
```cpp
// Post blinds
// In heads-up: position 0 = BB (acts first), position 1 = SB (acts second/button)
int bb = 0;  // First to act posts big blind
int sb = 1;  // Button posts small blind

// Post blinds (handle case where player doesn't have enough chips)
int sb_amount = std::min(config_.small_blind, stacks[sb]);
int bb_amount = std::min(config_.big_blind, stacks[bb]);

stacks[sb] -= sb_amount;
stacks[bb] -= bb_amount;

int pot = sb_amount + bb_amount;
```

## Improvements:

1. ✅ **Prevents negative stacks** - Uses `std::min()` to cap blinds at available chips
2. ✅ **Correct heads-up blind structure** - BB posts first, SB posts second
3. ✅ **Pot based on actual blinds** - Uses real posted amounts, not config values
4. ✅ **Short stack protection** - When a player goes broke, only posts what they have

## What You Need To Do:

**Recompile the C++ engine:**

```bash
cd "Heads-Up Poker"
python build_simple.py
```

OR if you have Visual Studio:
```bash
# Open Developer Command Prompt for VS
cd "C:\Users\Host\Documents\hva\Heads-Up Poker"
# Follow build instructions in README.md
```

## Testing After Fix:

Run V0 vs V0:
- Stacks should stay around 1000 each
- NO negative stacks
- Final stacks should sum to 2000 (total chips)
- Win rate should be ~50%

Run UI bot vs bot:
- No negative stack values
- Stacks displayed correctly
- Match completes without errors

## Why This Was Critical:

**Negative stacks break everything:**
- Can't calculate win rates correctly
- Can't compute profit/loss
- Shows incorrect match results
- Makes statistical analysis meaningless

**The fix ensures:**
- Stacks always >= 0
- Blinds rotate properly (handled by simulate_match's button rotation)
- Short-stack scenarios handled gracefully
- Accurate chip tracking throughout the match



