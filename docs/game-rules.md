# Heads-Up Poker: Game Rules

This document is the **canonical specification** for the simplified heads-up No-Limit Hold'em variant implemented by the C++ simulation engine and referenced by experiments, tests, and the research paper.

This is a **research abstraction**, not full multi-street Hold'em. Results apply only to the rules defined here.

## Overview

- **Players:** 2 (heads-up)
- **Streets:** 2 betting rounds — preflop and postflop
- **Board:** All five community cards are dealt at once before the postflop betting round (no separate flop/turn/river streets)
- **Deck:** Standard 52-card deck, no jokers
- **Default stacks:** 1000 chips per player (configurable)
- **Default blinds:** Small blind 10, big blind 20 (configurable)

## Card encoding and dealing

### Card representation

Cards are integers 0–51: `(rank_index * 4) + suit`, where rank_index is 0=2 … 12=A and suit is 0=clubs, 1=diamonds, 2=hearts, 3=spades.

### Dealing procedure

Each hand uses **exactly one shuffled 52-card deck**:

1. Build a deck of all 52 distinct cards.
2. Shuffle with the hand's deterministic RNG (seeded from match configuration).
3. Deal in order:
   - Player 0 hole cards: indices 0, 1
   - Player 1 hole cards: indices 2, 3
   - Board (5 cards): indices 4–8

**Invariant:** Every completed deal uses nine **unique** cards drawn without replacement from the same deck. Hole cards and board cannot overlap.

## Positions and blinds

Within each hand, after seat assignment:

| Seat index | Role        | Blind              |
|------------|-------------|--------------------|
| 0          | Small blind | Posts small blind  |
| 1          | Big blind   | Posts big blind    |

The **button** (dealer) alternates each hand in a match. When the button is on player *B*, seats are swapped so that player *B* occupies seat 0 (small blind) for that hand.

Blind posting:

- Each blind is `min(configured_blind, remaining_stack)`.
- Blinds are deducted from stacks and recorded as current street bets.
- If a stack is shorter than its blind, the player posts all remaining chips (all-in blind).

## Action order

| Betting round | First to act | Rationale                                      |
|---------------|--------------|------------------------------------------------|
| Preflop       | Seat 0 (SB)  | Standard heads-up: small blind acts first      |
| Postflop      | Seat 1 (BB)  | Standard heads-up: big blind acts first        |

Action alternates between players until the betting round completes or a player folds.

## Legal actions

On a player's turn, given `to_call = max(current_bets) - my_current_bet`:

| Action | Condition                                      |
|--------|------------------------------------------------|
| FOLD   | Always allowed when facing a bet               |
| CHECK  | Allowed only when `to_call == 0`               |
| CALL   | Allowed when `to_call > 0`; puts `min(to_call, stack)` into the pot |
| BET    | Allowed when `to_call == 0` and raises remain  |
| RAISE  | Allowed when `to_call > 0` and raises remain   |

Invalid checks (checking when facing a bet) are treated as **folds**.

### Bet and raise sizing

When betting or raising, the bot proposes a size; the engine enforces:

- **Minimum increment:** at least 1 chip beyond the amount to call, and at least the big blind when opening action.
- **Maximum:** cannot exceed remaining stack (all-in if insufficient).
- The player's new street total bet is the minimum of the desired total and `(current_bet + stack)`.

There is no fractional chip; all amounts are integers.

## Raise cap

- **Scope:** Per betting round (street), not per hand.
- **Limit:** At most **3 raises** (including the opening bet) per street.
- The cap **resets** between preflop and postflop.
- When the cap is reached, further BET/RAISE requests are converted to call (if facing a bet) or check (if not).

This matches the paper's "three-raise cap per betting round" description.

## All-in and unmatched bets

### Short stacks

- A call or raise never removes more chips than the player's remaining stack.
- A player with zero stack cannot act further.

### Unmatched (uncalled) bets

When betting ends with unequal street totals because one player could not match (all-in for less):

1. Compute the **matched amount** = `min(current_bets[0], current_bets[1])`.
2. Return the excess to the player who overbet: `current_bet - matched_amount` is refunded to their stack.
3. Only matched chips enter the pot for that street.

### Side pots

In heads-up, side pots arise only when both players are all-in for different amounts. The engine tracks a single main pot sufficient for equal matched contributions; unmatched excess is returned before pot settlement.

## Betting round completion

A betting round ends when:

1. A player **folds** (opponent wins immediately), or
2. Bets are **equalized** and the last aggressor has been called (neither player just raised), or
3. Both players are **all-in** for matched amounts, or
4. The **raise cap** is reached and remaining action resolves to call/check.

When a round completes without a fold, street bets are added to the running pot and street bet counters reset to zero.

## Showdown and pot settlement

### Fold

The non-folding player receives the entire pot (including all prior streets and current street bets).

### Showdown

After both betting rounds complete without a fold:

1. Each player forms the best 5-card hand from their 2 hole cards + 5 board cards (standard Hold'em evaluator).
2. Higher hand rank wins the pot.
3. **Ties:** Pot is split evenly. Any **odd chip** goes to seat 0 (lower index).

### Chip conservation invariant

At all times:

```
stacks[0] + stacks[1] + pot + current_bets[0] + current_bets[1] == 2 * initial_stack
```

No chips are created or destroyed except through blind posting, betting, refunds, and pot awards.

## Match rules

- A match plays up to `num_hands` hands or until either stack reaches zero.
- Button alternates each hand (`hand_index % 2`).
- **Match winner:** player with the larger final stack; tie if equal.

## Configuration reference

| Parameter              | Default | Description                          |
|------------------------|---------|--------------------------------------|
| `initial_stack`        | 1000    | Starting chips per player            |
| `small_blind`          | 10      | SB amount                          |
| `big_blind`            | 20      | BB amount                          |
| `max_raises_per_round` | 3       | Raise cap per street               |
| `seed`                 | 12345   | RNG seed for reproducible dealing  |

## Relationship to full Hold'em

Deliberately **not** modeled:

- Separate flop, turn, and river streets
- Multiway pots
- Straddle, ante, or rake
- Full side-pot layering beyond heads-up all-in cases
- Time banks or action clocks

Any experiment result is valid **only** under this specification until the engine, tests, and paper are aligned and experiments are rerun from versioned manifests.
