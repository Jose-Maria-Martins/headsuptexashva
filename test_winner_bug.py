#!/usr/bin/env python3
"""Test to see if winner and stacks are consistent."""

from poker_ai import poker_engine
from poker_ai.bots.monte_carlo_bot import MonteCarloBot
from poker_ai.bots.hand_strength_bot import HandStrengthBot

class WrappedBot(poker_engine.Bot):
    def __init__(self, impl):
        super().__init__()
        self._impl = impl
    
    def get_action(self, hole_cards, board, pot, to_call, stack, can_check):
        return self._impl.get_action(hole_cards, board, pot, to_call, stack, can_check)
    
    def get_bet_size(self, pot, stack):
        return self._impl.get_bet_size(pot, stack)

# Create config
config = poker_engine.SimConfig()
config.initial_stack = 1000
config.small_blind = 10
config.big_blind = 20
config.seed = 12345

# V2 vs V1
bot_v2 = WrappedBot(MonteCarloBot(42, rollouts=200))
bot_v1 = WrappedBot(HandStrengthBot(84))

# Create simulator
sim = poker_engine.Simulator(config)

# Run match
result = sim.simulate_match(bot_v2, bot_v1, 200)

print("=" * 60)
print("WINNER BUG TEST")
print("=" * 60)
print(f"P0 (V2) final stack: {result.p0_final_stack}")
print(f"P1 (V1) final stack: {result.p1_final_stack}")
print(f"Total chips: {result.p0_final_stack + result.p1_final_stack}")
print(f"\nP0 wins: {result.p0_wins}")
print(f"P1 wins: {result.p1_wins}")
print(f"Ties: {result.ties}")
print(f"Total hands: {result.hands_played}")
print(f"\nStack difference: {result.p0_final_stack - result.p1_final_stack}")

# Check consistency
if abs(result.p0_final_stack - result.p1_final_stack) > 500:
    if abs(result.p0_wins - result.p1_wins) < 10:
        print("\n[BUG DETECTED!]")
        print("Large stack difference but similar win counts!")
        print("This suggests winner tracking is wrong.")



