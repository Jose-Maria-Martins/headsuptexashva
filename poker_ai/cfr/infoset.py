import numpy as np
from typing import List, Dict, Tuple
import json

class InfoSet:
    """
    Stores regrets and strategies for a single information set.
    
    An information set is defined by:
    - Card bucket (preflop or postflop)
    - Betting round (0=preflop, 1=postflop)
    - Action history (encoded as string)
    - Position (0=SB, 1=BB)
    """
    
    def __init__(self, key: str, num_actions: int):
        """
        Initialize an information set.
        
        Args:
            key: Unique identifier for this infoset
            num_actions: Number of possible actions
        """
        self.key = key
        self.num_actions = num_actions
        
        # Cumulative regrets for each action
        self.regret_sum = np.zeros(num_actions, dtype=np.float64)
        
        # Cumulative strategy (for averaging)
        self.strategy_sum = np.zeros(num_actions, dtype=np.float64)
        
        # Current strategy (computed from regrets)
        self.strategy = np.ones(num_actions, dtype=np.float64) / num_actions
    
    def get_strategy(self, realization_weight: float = 1.0) -> np.ndarray:
        """
        Compute current strategy using regret matching.
        
        Regret matching: action probability proportional to positive regret.
        
        Args:
            realization_weight: Weight for strategy averaging
            
        Returns:
            Normalized probability distribution over actions
        """
        # Positive regrets only
        positive_regrets = np.maximum(self.regret_sum, 0.0)
        
        # Sum of positive regrets
        normalizing_sum = np.sum(positive_regrets)
        
        if normalizing_sum > 0:
            # Normalize to probability distribution
            self.strategy = positive_regrets / normalizing_sum
        else:
            # Uniform distribution if no positive regrets
            self.strategy = np.ones(self.num_actions, dtype=np.float64) / self.num_actions
        
        # Add to strategy sum for averaging
        self.strategy_sum += realization_weight * self.strategy
        
        return self.strategy.copy()
    
    def get_average_strategy(self) -> np.ndarray:
        """
        Get the average strategy over all iterations.
        
        This is the strategy we'll use in the final bot.
        
        Returns:
            Normalized average strategy
        """
        normalizing_sum = np.sum(self.strategy_sum)
        
        if normalizing_sum > 0:
            return self.strategy_sum / normalizing_sum
        else:
            # Uniform if never visited
            return np.ones(self.num_actions, dtype=np.float64) / self.num_actions
    
    def add_regret(self, action: int, regret: float):
        """
        Add regret for a specific action.
        
        Args:
            action: Action index
            regret: Regret value (can be negative)
        """
        self.regret_sum[action] += regret
    
    def to_dict(self) -> dict:
        """Serialize to dictionary for saving."""
        return {
            'key': self.key,
            'num_actions': self.num_actions,
            'regret_sum': self.regret_sum.tolist(),
            'strategy_sum': self.strategy_sum.tolist(),
        }
    
    @staticmethod
    def from_dict(data: dict) -> 'InfoSet':
        """Deserialize from dictionary."""
        infoset = InfoSet(data['key'], data['num_actions'])
        infoset.regret_sum = np.array(data['regret_sum'], dtype=np.float64)
        infoset.strategy_sum = np.array(data['strategy_sum'], dtype=np.float64)
        return infoset


class InfoSetManager:
    """
    Manages all information sets for CFR training.
    """
    
    def __init__(self):
        """Initialize empty infoset manager."""
        self.infosets: Dict[str, InfoSet] = {}
    
    def get_infoset(self, key: str, num_actions: int) -> InfoSet:
        """
        Get or create an information set.
        
        Args:
            key: Unique identifier
            num_actions: Number of legal actions
            
        Returns:
            InfoSet object
        """
        if key not in self.infosets:
            self.infosets[key] = InfoSet(key, num_actions)
        return self.infosets[key]
    
    def save(self, filepath: str):
        """
        Save all infosets to file.
        
        Args:
            filepath: Path to save JSON file
        """
        data = {
            'num_infosets': len(self.infosets),
            'infosets': {key: infoset.to_dict() for key, infoset in self.infosets.items()}
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load(self, filepath: str):
        """
        Load infosets from file.
        
        Args:
            filepath: Path to JSON file
        """
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        self.infosets = {
            key: InfoSet.from_dict(infoset_data)
            for key, infoset_data in data['infosets'].items()
        }
    
    def get_num_infosets(self) -> int:
        """Return total number of information sets."""
        return len(self.infosets)


def build_infoset_key(bucket: int, round: int, history: str, position: int) -> str:
    """
    Build a unique key for an information set.
    
    Args:
        bucket: Card bucket (0-4 preflop, 0-5 postflop)
        round: Betting round (0=preflop, 1=postflop)
        history: Action history string (e.g., "c", "br", "brc")
        position: Player position (0=SB, 1=BB)
        
    Returns:
        Unique string key
    """
    return f"{bucket}|{round}|{history}|{position}"




