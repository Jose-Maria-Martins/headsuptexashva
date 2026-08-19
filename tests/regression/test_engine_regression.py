"""Regression tests for known engine behaviour."""

from __future__ import annotations

import pytest

from tests.conftest import make_config, poker_engine, requires_engine
from tests.helpers.bots import AlwaysCheckBot


@requires_engine
def test_regression_hand_deal_seed_42():
    """Fixed-seed deal regression once engine is rebuilt."""
    cfg = make_config(seed=42)
    sim = poker_engine.Simulator(cfg)
    stacks = [cfg.initial_stack, cfg.initial_stack]
    result = sim.simulate_hand(
        AlwaysCheckBot(), AlwaysCheckBot(), stacks, button=0
    )
    cards = sorted(list(result.p0_hole) + list(result.p1_hole) + list(result.board))
    assert len(cards) == 9
    # Record observed board for this seed after first verified build
    assert hasattr(result, "board")


@requires_engine
@pytest.mark.regression
def test_v0_symmetry_smoke():
    """v0 vs v0 over small match should not diverge wildly (smoke only)."""
    from poker_ai.bots.random_bot import RandomBot

    class WrappedBot(poker_engine.Bot):
        def __init__(self, impl):
            super().__init__()
            self._impl = impl

        def get_action(self, hole_cards, board, pot, to_call, stack, can_check):
            return self._impl.get_action(hole_cards, board, pot, to_call, stack, can_check)

        def get_bet_size(self, pot, stack):
            return self._impl.get_bet_size(pot, stack)

    cfg = make_config(seed=1000)
    sim = poker_engine.Simulator(cfg)
    bot_a = WrappedBot(RandomBot(1000))
    bot_b = WrappedBot(RandomBot(2000))
    result = sim.simulate_match(bot_a, bot_b, num_hands=50)
    total = result.p0_wins + result.p1_wins
    if total > 0:
        rate = result.p0_wins / total
        assert 0.25 <= rate <= 0.75, f"v0 mirror too skewed: {rate:.2%}"
