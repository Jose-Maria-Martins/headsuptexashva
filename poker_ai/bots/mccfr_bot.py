from poker_ai import poker_engine
import numpy as np
import random
from typing import Optional, List
from poker_ai.cfr import CardAbstraction, ActionAbstraction, InfoSetManager, build_infoset_key


class MCCFRBot:
    """
    Experimental bot that uses a tabular CFR-trained strategy.
    
    This bot:
    - Queries a trained strategy blueprint
    - Uses card abstraction to bucket hands
    - Maps abstract actions to concrete bet sizes
    - Plays according to a learned strategy table when an information set exists
    - Falls back to a uniform legal policy for unseen information sets
    """
    
    def __init__(self, strategy_path: str, player_id: int = 0, seed: Optional[int] = None):
        """
        Initialize MCCFR bot with trained strategy.
        
        Args:
            strategy_path: Path to trained strategy JSON file
            player_id: Player identifier
            seed: Random seed for action sampling
        """
        self.player_id = player_id
        self.rng = np.random.default_rng(seed if seed is not None else 42)
        self.name = "MCCFRBot"
        
        # Load trained strategy
        self.infoset_manager = InfoSetManager()
        self.infoset_manager.load(strategy_path)
        
        # Track game history for this hand
        self.current_history = ""
        self.current_round = 0
        self.position = 0  # Will be set in reset()
    
    def reset(self):
        """Reset for new hand."""
        self.current_history = ""
        self.current_round = 0
    
    def set_position(self, is_button: bool):
        """
        Set position for this hand.
        
        Args:
            is_button: True if this player is button (acts last postflop)
        """
        # In heads-up: button = SB (acts first preflop, last postflop)
        # We track position as 0=SB, 1=BB for infoset keys
        self.position = 0 if is_button else 1
    
    def get_action(self, hole_cards: List[int], board: List[int], 
                   pot: int, to_call: int, stack: int, can_check: bool,
                   opp_stack: int = 1000, big_blind: int = 20, initial_stack: int = 1000) -> str:
        """
        Get action using trained CFR strategy.
        
        Args:
            hole_cards: Player's hole cards
            board: Community cards
            can_check: True if checking is allowed
            to_call: Amount needed to call
            pot: Current pot size
            my_stack: Player's remaining stack
            opp_stack: Opponent's stack
            big_blind: Big blind size
            initial_stack: Starting stack
            
        Returns:
            'FOLD', 'CALL', or 'RAISE'
        """
        # Determine round
        if len(board) == 0:
            round_num = 0  # Preflop
        else:
            round_num = 1  # Postflop
        
        # Update round tracking
        # A fold can end a hand before the postflop round is reached. Reset the
        # action history at the next preflop decision so it cannot leak across
        # hands when the caller does not expose an explicit hand boundary.
        if (
            round_num != self.current_round
            or (round_num == 0 and self.current_history.endswith("f"))
        ):
            self.current_round = round_num
            self.current_history = ""  # Reset history for new round
        
        # Get card bucket
        if round_num == 0:
            bucket = CardAbstraction.get_preflop_bucket(hole_cards)
        else:
            bucket = CardAbstraction.get_postflop_bucket(hole_cards, board)
        
        # Build infoset key
        infoset_key = build_infoset_key(bucket, round_num, self.current_history, self.position)
        
        # Get legal actions
        legal_actions = ActionAbstraction.get_legal_actions(can_check, to_call)
        
        # Query strategy
        if infoset_key in self.infoset_manager.infosets:
            infoset = self.infoset_manager.infosets[infoset_key]
            strategy = infoset.get_average_strategy()
        else:
            # Unseen infoset - use uniform strategy over legal actions
            strategy = np.ones(4, dtype=np.float64) / 4
        
        # Filter to legal actions and renormalize
        legal_probs = np.zeros(len(legal_actions))
        for i, action in enumerate(legal_actions):
            if action < len(strategy):
                legal_probs[i] = strategy[action]
            else:
                legal_probs[i] = 1.0 / len(legal_actions)  # Uniform fallback
        
        total = np.sum(legal_probs)
        if total > 0:
            legal_probs /= total
        else:
            # Uniform fallback
            legal_probs = np.ones(len(legal_actions)) / len(legal_actions)
        
        # Sample action according to strategy
        action_idx = self.rng.choice(len(legal_actions), p=legal_probs)
        action = legal_actions[action_idx]
        
        # Get Action enum
        from poker_ai import poker_engine
        Action = poker_engine.Action
        
        # Record action in history and return appropriate Action
        if action == ActionAbstraction.FOLD:
            self.current_history += 'f'
            return Action.FOLD
        elif action == ActionAbstraction.CALL:
            self.current_history += 'c'
            if can_check:
                return Action.CHECK
            else:
                return Action.CALL
        else:  # BET_HALF or BET_POT
            self.current_history += 'b'
            
            # Store bet size for get_bet_size()
            self._last_action = action
            self._last_pot = pot
            self._last_to_call = to_call
            self._last_stack = stack
            
            if can_check:
                return Action.BET
            else:
                return Action.RAISE
    
    def get_bet_size(self, pot: int, stack: int) -> int:
        """
        Get bet size based on abstract action.
        
        Args:
            pot: Current pot
            stack: Player's stack
            
        Returns:
            Bet amount in chips
        """
        # Use stored action from get_action()
        action = getattr(self, '_last_action', ActionAbstraction.BET_POT)
        to_call = getattr(self, '_last_to_call', 0)
        
        # Calculate bet size
        bet_size = ActionAbstraction.action_to_bet_size(
            action, pot, to_call, stack
        )
        
        # Ensure minimum bet (at least 20)
        if bet_size > 0:
            bet_size = max(bet_size, 20)
        
        # Cap at stack
        bet_size = min(bet_size, stack)
        
        return int(bet_size)
