"""Adapter for the experimental tabular CFR policy."""

from __future__ import annotations

from typing import Optional, Sequence

import numpy as np

from poker_ai import poker_engine
from poker_ai.cfr import ActionAbstraction, CardAbstraction, InfoSetManager, build_infoset_key


class MCCFRBot:
    """Small v3 policy adapter; this is not a mature GTO solver."""

    def __init__(self, strategy_path: str, player_id: int = 0, seed: Optional[int] = None):
        self.player_id = player_id
        self.rng = np.random.default_rng(seed)
        self.infosets = InfoSetManager()
        self.infosets.load(strategy_path)
        self.position = 0
        self.round = 0
        self.history = ""
        self._last_action = ActionAbstraction.BET_POT
        self._last_to_call = 0

    def reset(self) -> None:
        """Start a new hand."""
        self.round = 0
        self.history = ""
        self._last_action = ActionAbstraction.BET_POT
        self._last_to_call = 0

    def set_position(self, is_button: bool) -> None:
        """Set the strategy position (button/SB is position 0)."""
        self.position = 0 if is_button else 1

    def _strategy(self, key: str, legal: Sequence[int]) -> np.ndarray:
        info = self.infosets.infosets.get(key)
        if info is None:
            return np.full(len(legal), 1.0 / len(legal))
        values = np.asarray(info.get_average_strategy(), dtype=float)
        probabilities = np.array(
            [values[action] if action < len(values) else 0.0 for action in legal],
            dtype=float,
        )
        total = probabilities.sum()
        return probabilities / total if total > 0 else np.full(len(legal), 1.0 / len(legal))

    def get_action(
        self,
        hole_cards: Sequence[int],
        board: Sequence[int],
        pot: int,
        to_call: int,
        stack: int,
        can_check: bool,
        **_: int,
    ) -> poker_engine.Action:
        """Choose one legal engine action from the learned abstract policy."""
        current_round = 0 if not board else 1
        if current_round != self.round or (current_round == 0 and self.history.endswith("f")):
            self.round = current_round
            self.history = ""
        cards = list(hole_cards)
        visible_board = list(board)
        bucket = (
            CardAbstraction.get_preflop_bucket(cards)
            if current_round == 0
            else CardAbstraction.get_postflop_bucket(cards, visible_board)
        )
        call_amount = max(0, to_call)
        legal = ActionAbstraction.get_legal_actions(can_check, call_amount)
        key = build_infoset_key(bucket, current_round, self.history, self.position)
        abstract_action = legal[int(self.rng.choice(len(legal), p=self._strategy(key, legal)))]
        self._last_action = abstract_action
        self._last_to_call = call_amount

        if abstract_action == ActionAbstraction.FOLD:
            self.history += "f"
            return poker_engine.Action.FOLD
        if abstract_action == ActionAbstraction.CALL:
            self.history += "c"
            return poker_engine.Action.CHECK if can_check else poker_engine.Action.CALL
        self.history += "b"
        return poker_engine.Action.BET if can_check else poker_engine.Action.RAISE

    def get_bet_size(self, pot: int, stack: int) -> int:
        """Map the last abstract bet to a bounded chip amount."""
        available = max(0, stack)
        amount = ActionAbstraction.action_to_bet_size(
            self._last_action, pot, self._last_to_call, available
        )
        return int(min(max(amount, 20), available)) if amount > 0 else 0
