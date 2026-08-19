"""Shared pytest fixtures and helpers."""

from __future__ import annotations

import pytest

try:
    from poker_ai import poker_engine

    ENGINE_AVAILABLE = True
except ImportError:
    ENGINE_AVAILABLE = False
    poker_engine = None  # type: ignore


requires_engine = pytest.mark.skipif(
    not ENGINE_AVAILABLE,
    reason="C++ poker_engine module not built (run build_simple.py or cmake)",
)


# Known hand fixtures (card strings)
HIGH_CARD_A = ["As", "Kd", "9c", "5h", "3s", "2d", "7c"]
PAIR_KINGS = ["Ks", "Kh", "9c", "5h", "3s", "2d", "7c"]
STRAIGHT = ["9h", "8d", "7c", "6s", "5h", "2d", "3c"]
FLUSH = ["Ah", "Kh", "9h", "5h", "3h", "2d", "7c"]
FULL_HOUSE = ["Ks", "Kh", "9c", "9d", "9h", "2s", "3c"]


def make_config(seed: int = 42, **overrides):
    cfg = poker_engine.SimConfig()
    cfg.initial_stack = overrides.get("initial_stack", 1000)
    cfg.small_blind = overrides.get("small_blind", 10)
    cfg.big_blind = overrides.get("big_blind", 20)
    cfg.max_raises_per_round = overrides.get("max_raises_per_round", 3)
    cfg.seed = seed
    return cfg


def total_chips(stacks, pot: int = 0, current_bets=None) -> int:
    bets = sum(current_bets or [0, 0])
    return stacks[0] + stacks[1] + pot + bets
