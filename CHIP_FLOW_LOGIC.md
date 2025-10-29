# Correct Chip Flow Logic

## How Chips Should Move in Poker

### Initial State
- Player 0: 1000 chips
- Player 1: 1000 chips
- **TOTAL: 2000 chips** (this must NEVER change)

### Step 1: Post Blinds
```
Player 0 posts SB (10): stack[0] = 990, current_bets[0] = 10
Player 1 posts BB (20): stack[1] = 980, current_bets[1] = 20
POT = 0 (chips are in current_bets, not pot yet!)
```

### Step 2: Betting Round
All actions add to `current_bets`, subtract from `stack`:

**Call**:
```
to_call = max(current_bets) - current_bets[player]
current_bets[player] += to_call
stack[player] -= to_call
```

**Raise to X**:
```
additional = X - current_bets[player]
current_bets[player] = X
stack[player] -= additional  // ONLY the additional amount!
```

### Step 3: End of Betting Round
```
pot += current_bets[0] + current_bets[1]  // Move all bets to pot
current_bets[0] = 0
current_bets[1] = 0
```

### Step 4: Next Betting Round (or Showdown)
Repeat steps 2-3, OR award pot to winner

### Step 5: Award Pot
```
stack[winner] += pot
pot = 0
```

## Invariant (ALWAYS TRUE)
```
stack[0] + stack[1] + pot + current_bets[0] + current_bets[1] = 2000
```

## Common Bugs

### Bug 1: Double-counting blinds
```cpp
// WRONG:
pot = sb + bb;  // Blinds in pot
current_bets = {sb, bb};  // Blinds also in current_bets!
// Later: pot += current_bets[0] + current_bets[1];  // DOUBLE!

// CORRECT:
pot = 0;
current_bets = {sb, bb};  // Blinds only here
// Later: pot += current_bets[0] + current_bets[1];  // OK
```

### Bug 2: Wrong raise amount
```cpp
// WRONG:
current_bets[player] = new_total;
stack[player] -= new_total;  // Subtracts entire total!

// CORRECT:
additional = new_total - current_bets[player];
current_bets[player] = new_total;
stack[player] -= additional;  // Only subtract what's new
```

### Bug 3: Not resetting current_bets
```cpp
// At end of each betting round:
pot += current_bets[0] + current_bets[1];
current_bets[0] = 0;  // MUST reset!
current_bets[1] = 0;  // MUST reset!
```



