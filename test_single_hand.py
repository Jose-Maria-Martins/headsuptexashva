#!/usr/bin/env python3
"""Test a single hand to debug chip flow."""

from poker_ai import poker_engine
from poker_ai.bots.random_bot import RandomBot

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

# Create bots
bot_a = WrappedBot(RandomBot(42))
bot_b = WrappedBot(RandomBot(84))

# Create simulator
sim = poker_engine.Simulator(config)

# Run 200 hands to thoroughly test
result = sim.simulate_match(bot_a, bot_b, 200)

print(f"Hands played: {result.hands_played}")
print(f"P0 final stack: {result.p0_final_stack}")
print(f"P1 final stack: {result.p1_final_stack}")
print(f"Total chips: {result.p0_final_stack + result.p1_final_stack}")
print(f"Missing: {2000 - (result.p0_final_stack + result.p1_final_stack)} chips")

if result.p0_final_stack + result.p1_final_stack != 2000:
    print(f"\n❌ CHIP LEAK! Missing {2000 - (result.p0_final_stack + result.p1_final_stack)} chips!")
else:
    print(f"\nOK Chips conserved!")

