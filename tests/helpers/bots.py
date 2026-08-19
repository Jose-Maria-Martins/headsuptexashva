"""Test bot helpers for integration and contract tests."""

from __future__ import annotations

from poker_ai import poker_engine


class AlwaysFoldBot(poker_engine.Bot):
    def get_action(self, hole_cards, board, pot, to_call, stack, can_check):
        return poker_engine.Action.FOLD

    def get_bet_size(self, pot, stack):
        return 0


class AlwaysCheckBot(poker_engine.Bot):
    def get_action(self, hole_cards, board, pot, to_call, stack, can_check):
        if can_check:
            return poker_engine.Action.CHECK
        return poker_engine.Action.CALL

    def get_bet_size(self, pot, stack):
        return 0


class AlwaysCallBot(poker_engine.Bot):
    def get_action(self, hole_cards, board, pot, to_call, stack, can_check):
        if can_check:
            return poker_engine.Action.CHECK
        return poker_engine.Action.CALL

    def get_bet_size(self, pot, stack):
        return 0


class SequenceRecordingBot(poker_engine.Bot):
    """Records which player acts on each street."""

    def __init__(self, player_id: int, sequence: list, fallback=None):
        super().__init__()
        self.player_id = player_id
        self.sequence = sequence
        self.fallback = fallback or AlwaysCheckBot()

    def get_action(self, hole_cards, board, pot, to_call, stack, can_check):
        street = "postflop" if board else "preflop"
        self.sequence.append((street, self.player_id))
        return self.fallback.get_action(hole_cards, board, pot, to_call, stack, can_check)

    def get_bet_size(self, pot, stack):
        return self.fallback.get_bet_size(pot, stack)


class FirstActionFolderBot(poker_engine.Bot):
    """Folds on first decision; checks/calls otherwise."""

    def __init__(self):
        super().__init__()
        self.acted = False

    def get_action(self, hole_cards, board, pot, to_call, stack, can_check):
        if not self.acted:
            self.acted = True
            return poker_engine.Action.FOLD
        return poker_engine.Action.CHECK

    def get_bet_size(self, pot, stack):
        return 0
