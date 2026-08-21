"""Copy this file when adding a new research bot.

The template is documentation-first: implement the two methods, then add the
bot to the package exports and write tests before benchmarking it.
"""

from __future__ import annotations

from typing import Sequence

from poker_ai import poker_engine


class NewBot:
    """One-sentence description of the policy and its limitations."""

    name = "NewBot"

    def __init__(self, seed: int = 0) -> None:
        # Store a seeded random.Random or numpy Generator if needed.
        self.seed = seed

    def get_action(
        self,
        hole_cards: Sequence[int],
        board: Sequence[int],
        pot: int,
        to_call: int,
        stack: int,
        can_check: bool,
    ) -> poker_engine.Action:
        """Return one legal engine action."""
        raise NotImplementedError("Implement the policy decision here")

    def get_bet_size(self, pot: int, stack: int) -> int:
        """Return a positive, stack-bounded amount after BET/RAISE."""
        raise NotImplementedError("Implement bet sizing here")
