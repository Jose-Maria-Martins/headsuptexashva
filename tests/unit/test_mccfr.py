"""Focused tests for the small, experimental CFR policy."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from poker_ai import poker_engine
from poker_ai.bots.mccfr_bot import MCCFRBot
from poker_ai.cfr.trainer import MCCFRTrainer

STRATEGY_PATH = Path(__file__).parents[2] / "poker_ai" / "cfr" / "strategy.json"


def test_seeded_trainer_is_reproducible():
    first = MCCFRTrainer(seed=7)
    second = MCCFRTrainer(seed=7)
    first.train(2, verbose=False)
    second.train(2, verbose=False)

    assert set(first.infoset_manager.infosets) == set(second.infoset_manager.infosets)
    for key in first.infoset_manager.infosets:
        a = first.infoset_manager.infosets[key]
        b = second.infoset_manager.infosets[key]
        np.testing.assert_array_equal(a.regret_sum, b.regret_sum)
        np.testing.assert_array_equal(a.strategy_sum, b.strategy_sum)


def test_mccfr_bot_returns_engine_actions():
    bot = MCCFRBot(str(STRATEGY_PATH), seed=7)
    action = bot.get_action(
        hole_cards=[0, 5],
        board=[],
        pot=30,
        to_call=10,
        stack=1000,
        can_check=False,
    )

    assert action in (
        poker_engine.Action.FOLD,
        poker_engine.Action.CALL,
        poker_engine.Action.RAISE,
    )


def test_mccfr_bot_bet_size_is_bounded():
    bot = MCCFRBot(str(STRATEGY_PATH), seed=7)
    bot.get_action([0, 5], [], 30, 0, 100, True)
    assert 0 <= bot.get_bet_size(30, 100) <= 100
