"""Property and conservation tests for the simulation engine."""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from tests.conftest import make_config, poker_engine, requires_engine, total_chips
from tests.helpers.bots import AlwaysCallBot, AlwaysCheckBot, AlwaysFoldBot


def _hand_cards_unique(result) -> bool:
    cards = list(result.p0_hole) + list(result.p1_hole) + list(result.board)
    return len(cards) == 9 and len(set(cards)) == 9


@requires_engine
class TestCardUniqueness:
    def test_single_hand_nine_unique_cards(self):
        cfg = make_config(seed=123)
        sim = poker_engine.Simulator(cfg)
        stacks = [cfg.initial_stack, cfg.initial_stack]
        result = sim.simulate_hand(
            AlwaysCheckBot(), AlwaysCheckBot(), stacks, button=0
        )
        assert _hand_cards_unique(result)

    @given(st.integers(min_value=0, max_value=10_000))
    @settings(max_examples=25, deadline=None)
    def test_many_hands_unique_cards(self, seed):
        cfg = make_config(seed=seed)
        sim = poker_engine.Simulator(cfg)
        stacks = [cfg.initial_stack, cfg.initial_stack]
        for button in (0, 1):
            stacks = [cfg.initial_stack, cfg.initial_stack]
            result = sim.simulate_hand(
                AlwaysCheckBot(), AlwaysCheckBot(), stacks, button=button
            )
            assert _hand_cards_unique(result)


@requires_engine
class TestChipConservation:
    def test_check_down_hand_conserves_chips(self):
        cfg = make_config(seed=99)
        initial_total = 2 * cfg.initial_stack
        sim = poker_engine.Simulator(cfg)
        stacks = [cfg.initial_stack, cfg.initial_stack]
        sim.simulate_hand(AlwaysCheckBot(), AlwaysCheckBot(), stacks, button=0)
        assert sum(stacks) == initial_total

    def test_fold_preserves_chips(self):
        cfg = make_config(seed=101)
        initial_total = 2 * cfg.initial_stack
        sim = poker_engine.Simulator(cfg)
        stacks = [cfg.initial_stack, cfg.initial_stack]
        sim.simulate_hand(AlwaysFoldBot(), AlwaysCallBot(), stacks, button=0)
        assert sum(stacks) == initial_total

    def test_match_conserves_chips(self):
        cfg = make_config(seed=202)
        initial_total = 2 * cfg.initial_stack
        sim = poker_engine.Simulator(cfg)
        result = sim.simulate_match(
            AlwaysCheckBot(), AlwaysCheckBot(), num_hands=20
        )
        assert result.p0_final_stack + result.p1_final_stack == initial_total


@requires_engine
class TestNonNegativeState:
    @given(st.integers(min_value=1, max_value=5000))
    @settings(max_examples=10, deadline=None)
    def test_stacks_never_negative_after_match(self, seed):
        cfg = make_config(seed=seed)
        sim = poker_engine.Simulator(cfg)
        result = sim.simulate_match(
            AlwaysCallBot(), AlwaysCallBot(), num_hands=5
        )
        assert result.p0_final_stack >= 0
        assert result.p1_final_stack >= 0
