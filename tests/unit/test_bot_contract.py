"""Common interface checks for every shipped bot policy."""

from pathlib import Path

from poker_ai import poker_engine
from poker_ai.bots import HandStrengthBot, MCCFRBot, MonteCarloBot, RandomBot


STRATEGY_PATH = Path(__file__).parents[2] / "poker_ai" / "cfr" / "strategy.json"


def test_all_bots_return_legal_actions_and_bounded_bets():
    bots = [
        RandomBot(seed=1),
        HandStrengthBot(seed=1),
        MonteCarloBot(seed=1),
        MCCFRBot(str(STRATEGY_PATH), seed=1),
    ]
    legal = {poker_engine.Action.FOLD, poker_engine.Action.CALL,
             poker_engine.Action.CHECK, poker_engine.Action.BET,
             poker_engine.Action.RAISE}

    for bot in bots:
        action = bot.get_action([0, 1], [], 30, 10, 100, False)
        assert action in legal
        amount = bot.get_bet_size(30, 100)
        assert 0 <= amount <= 100


def test_seeded_random_bots_are_repeatable():
    first = RandomBot(seed=9)
    second = RandomBot(seed=9)
    actions_a = [first.get_action([0, 1], [], 30, 10, 100, False) for _ in range(10)]
    actions_b = [second.get_action([0, 1], [], 30, 10, 100, False) for _ in range(10)]
    assert actions_a == actions_b
