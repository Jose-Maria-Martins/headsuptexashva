"""
Counterfactual Regret Minimization (CFR) implementation for poker AI.
"""

from .abstraction import CardAbstraction, ActionAbstraction
from .infoset import InfoSet, InfoSetManager, build_infoset_key
from .trainer import MCCFRTrainer

__all__ = [
    "CardAbstraction",
    "ActionAbstraction",
    "InfoSet",
    "InfoSetManager",
    "build_infoset_key",
    "MCCFRTrainer",
]

