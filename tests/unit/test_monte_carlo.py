"""Focused tests for the calibrated v2 preflop policy."""

from poker_ai import poker_engine
from poker_ai.bots.monte_carlo_bot import MonteCarloBot


def test_monte_carlo_preflop_policy_uses_calibrated_thresholds():
    bot = MonteCarloBot(seed=1)

    assert bot.get_action([0, 1], [], 30, 0, 1000, True) == poker_engine.Action.CHECK
    assert bot.get_action([0, 1], [], 30, 10, 1000, False) == poker_engine.Action.FOLD
    assert bot.get_action([48, 49], [], 30, 0, 1000, True) == poker_engine.Action.BET
    assert bot.get_action([48, 49], [], 30, 10, 1000, False) == poker_engine.Action.RAISE
