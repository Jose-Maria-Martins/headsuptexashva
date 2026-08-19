"""Card parsing and hand evaluator unit tests."""

from __future__ import annotations

import pytest

from tests.conftest import (
    ENGINE_AVAILABLE,
    FLUSH,
    FULL_HOUSE,
    HIGH_CARD_A,
    PAIR_KINGS,
    STRAIGHT,
    poker_engine,
    requires_engine,
)

ALL_RANKS = "23456789TJQKA"
ALL_SUITS = "cdhs"


@requires_engine
class TestCardParsing:
    def test_all_52_cards_roundtrip(self):
        for rank in ALL_RANKS:
            for suit in ALL_SUITS:
                card_str = rank + suit
                card_id = poker_engine.string_to_card(card_str)
                assert poker_engine.card_to_string(card_id) == card_str

    def test_invalid_card_string_raises(self):
        with pytest.raises(Exception):
            poker_engine.string_to_card("X")

    def test_rank_and_suit_helpers(self):
        ace_spades = poker_engine.string_to_card("As")
        assert poker_engine.get_rank(ace_spades) == 12
        assert poker_engine.get_suit(ace_spades) == 3


@requires_engine
class TestHandEvaluator:
    def test_high_card(self):
        score = poker_engine.HandEvaluator.evaluate(
            [poker_engine.string_to_card(c) for c in HIGH_CARD_A]
        )
        assert poker_engine.HandEvaluator.get_hand_rank(score) == poker_engine.HandRank.HIGH_CARD

    def test_pair_beats_high_card(self):
        pair_score = poker_engine.HandEvaluator.evaluate(
            [poker_engine.string_to_card(c) for c in PAIR_KINGS]
        )
        high_score = poker_engine.HandEvaluator.evaluate(
            [poker_engine.string_to_card(c) for c in HIGH_CARD_A]
        )
        assert pair_score > high_score

    def test_straight_beats_pair(self):
        straight_score = poker_engine.HandEvaluator.evaluate(
            [poker_engine.string_to_card(c) for c in STRAIGHT]
        )
        pair_score = poker_engine.HandEvaluator.evaluate(
            [poker_engine.string_to_card(c) for c in PAIR_KINGS]
        )
        assert straight_score > pair_score

    def test_flush_beats_straight(self):
        flush_score = poker_engine.HandEvaluator.evaluate(
            [poker_engine.string_to_card(c) for c in FLUSH]
        )
        straight_score = poker_engine.HandEvaluator.evaluate(
            [poker_engine.string_to_card(c) for c in STRAIGHT]
        )
        assert flush_score > straight_score

    def test_full_house_beats_flush(self):
        fh_score = poker_engine.HandEvaluator.evaluate(
            [poker_engine.string_to_card(c) for c in FULL_HOUSE]
        )
        flush_score = poker_engine.HandEvaluator.evaluate(
            [poker_engine.string_to_card(c) for c in FLUSH]
        )
        assert fh_score > flush_score

    def test_evaluate_hand_string_helper(self):
        score, desc = poker_engine.evaluate_hand_string(PAIR_KINGS)
        assert score > 0
        assert isinstance(desc, str)


def test_engine_import_smoke():
    if not ENGINE_AVAILABLE:
        pytest.skip("engine not built")
    assert poker_engine.Action.FOLD is not None
