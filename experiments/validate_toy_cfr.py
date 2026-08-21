"""Small Kuhn/Leduc CFR sanity checks.

These games are intentionally separate from the Hold'em trainer. They provide
known tiny imperfect-information environments in which regret matching should
produce low regret before stronger v3 claims.
"""

from __future__ import annotations

import argparse
import random
from collections import defaultdict


class ToyCFR:
    def __init__(self, game: str, seed: int = 7):
        self.game = game
        self.rng = random.Random(seed)
        self.regret = defaultdict(lambda: [0.0, 0.0])
        self.strategy_sum = defaultdict(lambda: [0.0, 0.0])
        self.iterations = 0

    def _strategy(self, key: str, reach: float) -> list[float]:
        positive = [max(value, 0.0) for value in self.regret[key]]
        total = sum(positive)
        strategy = [value / total for value in positive] if total else [0.5, 0.5]
        for i, probability in enumerate(strategy):
            self.strategy_sum[key][i] += reach * probability
        return strategy

    def average(self, key: str) -> list[float]:
        values = self.strategy_sum[key]
        total = sum(values)
        return [value / total for value in values] if total else [0.5, 0.5]

    @staticmethod
    def _actions(history: str) -> tuple[str, str]:
        return {"": ("c", "b"), "c": ("c", "b"), "b": ("c", "f"), "cb": ("c", "f")}[
            history
        ]

    @staticmethod
    def _kuhn_terminal(cards: tuple[int, int], history: str) -> int | None:
        if history in ("bc", "cbc"):
            return 2 if cards[0] > cards[1] else -2
        if history == "cc":
            return 1 if cards[0] > cards[1] else -1
        if history == "bf":
            return 1
        if history == "cbf":
            return -1
        return None

    def _kuhn_cfr(self, cards: tuple[int, int], history: str, p0: float, p1: float, player: int) -> float:
        utility = self._kuhn_terminal(cards, history)
        if utility is not None:
            return float(utility if player == 0 else -utility)
        actor = 0 if history in ("", "cb") else 1
        actions = self._actions(history)
        key = f"k:{actor}:{cards[actor]}:{history}"
        strategy = self._strategy(key, p0 if actor == 0 else p1)
        values = [
            self._kuhn_cfr(
                cards,
                history + action,
                p0 * strategy[i] if actor == 0 else p0,
                p1 * strategy[i] if actor == 1 else p1,
                player,
            )
            for i, action in enumerate(actions)
        ]
        expected = sum(strategy[i] * values[i] for i in range(2))
        if actor == player:
            reach = p1 if actor == 0 else p0
            for i in range(2):
                self.regret[key][i] += reach * (values[i] - expected)
        return expected

    @staticmethod
    def _leduc_terminal(cards: tuple[int, int], board: int | None, round_no: int, history: str) -> int | None:
        if history == "bf":
            return 1
        if history == "cbf":
            return -1
        if round_no == 1 and history in ("cc", "bc", "cbc"):
            assert board is not None
            if (cards[0] == board) != (cards[1] == board):
                winner = 1 if cards[0] == board else -1
            else:
                winner = 1 if cards[0] > cards[1] else -1
            return winner * (1 if history == "cc" else 2)
        return None

    def _leduc_cfr(
        self,
        cards: tuple[int, int],
        board: int | None,
        round_no: int,
        history: str,
        p0: float,
        p1: float,
        player: int,
    ) -> float:
        utility = self._leduc_terminal(cards, board, round_no, history)
        if utility is not None:
            return float(utility if player == 0 else -utility)
        if round_no == 0 and history in ("cc", "bc", "cbc"):
            remaining = [card for card in (0, 0, 1, 1, 2, 2) if card not in cards]
            board = self.rng.choice(remaining)
            return self._leduc_cfr(cards, board, 1, "", p0, p1, player)
        actor = 0 if history in ("", "cb") else 1
        bucket = board if board is not None else -1
        key = f"l:{actor}:{cards[actor]}:{bucket}:{round_no}:{history}"
        strategy = self._strategy(key, p0 if actor == 0 else p1)
        values = [
            self._leduc_cfr(
                cards,
                board,
                round_no,
                history + action,
                p0 * strategy[i] if actor == 0 else p0,
                p1 * strategy[i] if actor == 1 else p1,
                player,
            )
            for i, action in enumerate(self._actions(history))
        ]
        expected = sum(strategy[i] * values[i] for i in range(2))
        if actor == player:
            reach = p1 if actor == 0 else p0
            for i in range(2):
                self.regret[key][i] += reach * (values[i] - expected)
        return expected

    def train(self, iterations: int) -> None:
        for _ in range(iterations):
            if self.game == "kuhn":
                cards = tuple(self.rng.sample([0, 1, 2], 2))
                for player in (0, 1):
                    self._kuhn_cfr(cards, "", 1.0, 1.0, player)
            else:
                cards = tuple(self.rng.sample([0, 0, 1, 1, 2, 2], 2))
                for player in (0, 1):
                    self._leduc_cfr(cards, None, 0, "", 1.0, 1.0, player)
        self.iterations += iterations

    def report(self) -> dict[str, float | int]:
        regrets = [sum(abs(value) for value in values) for values in self.regret.values()]
        return {
            "iterations": self.iterations,
            "infosets": len(self.regret),
            "mean_absolute_regret": sum(regrets) / len(regrets) if regrets else 0.0,
            "mean_regret_per_iteration": (
                sum(regrets) / len(regrets) / max(1, self.iterations) if regrets else 0.0
            ),
        }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--iterations", type=int, default=20000)
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()
    for game in ("kuhn", "leduc"):
        trainer = ToyCFR(game, seed=args.seed)
        trainer.train(args.iterations)
        print(f"{game}: {trainer.report()}")


if __name__ == "__main__":
    main()
