"""Integration tests for betting rules and action order."""

from __future__ import annotations

from tests.conftest import make_config, poker_engine, requires_engine
from tests.helpers.bots import (
    AlwaysCallBot,
    AlwaysCheckBot,
    AlwaysFoldBot,
    SequenceRecordingBot,
)


@requires_engine
class TestActionOrder:
    def test_preflop_small_blind_acts_first(self):
        sequence: list = []
        cfg = make_config(seed=7)
        sim = poker_engine.Simulator(cfg)
        stacks = [cfg.initial_stack, cfg.initial_stack]
        bot0 = SequenceRecordingBot(0, sequence, AlwaysCheckBot())
        bot1 = SequenceRecordingBot(1, sequence, AlwaysCheckBot())
        sim.simulate_hand(bot0, bot1, stacks, button=0)
        preflop_order = [pid for street, pid in sequence if street == "preflop"]
        assert preflop_order[0] == 0

    def test_postflop_big_blind_acts_first(self):
        sequence: list = []
        cfg = make_config(seed=8)
        sim = poker_engine.Simulator(cfg)
        stacks = [cfg.initial_stack, cfg.initial_stack]
        bot0 = SequenceRecordingBot(0, sequence, AlwaysCheckBot())
        bot1 = SequenceRecordingBot(1, sequence, AlwaysCheckBot())
        sim.simulate_hand(bot0, bot1, stacks, button=0)
        postflop_order = [pid for street, pid in sequence if street == "postflop"]
        assert len(postflop_order) >= 1
        assert postflop_order[0] == 1


@requires_engine
class TestBettingOutcomes:
    def test_fold_awards_pot_to_caller(self):
        cfg = make_config(seed=11)
        sim = poker_engine.Simulator(cfg)
        stacks = [cfg.initial_stack, cfg.initial_stack]
        result = sim.simulate_hand(
            AlwaysFoldBot(), AlwaysCallBot(), stacks, button=0
        )
        assert result.winner == 1
        assert stacks[1] > cfg.initial_stack

    def test_showdown_produces_rank_fields(self):
        cfg = make_config(seed=12)
        sim = poker_engine.Simulator(cfg)
        stacks = [cfg.initial_stack, cfg.initial_stack]
        result = sim.simulate_hand(
            AlwaysCheckBot(), AlwaysCheckBot(), stacks, button=0
        )
        assert result.p0_showdown_rank >= 0
        assert result.p1_showdown_rank >= 0


@requires_engine
class TestDeterministicReplay:
    def test_same_seed_same_winner(self):
        cfg = make_config(seed=4242)

        def run_once():
            sim = poker_engine.Simulator(cfg)
            stacks = [cfg.initial_stack, cfg.initial_stack]
            return sim.simulate_hand(
                AlwaysCheckBot(), AlwaysCheckBot(), stacks, button=0
            )

        r1 = run_once()
        r2 = run_once()
        assert r1.winner == r2.winner
        assert list(r1.board) == list(r2.board)
        assert list(r1.p0_hole) == list(r2.p0_hole)
