from poker_ai import poker_engine
from typing import List, Tuple, Set
import random


class CardAbstraction:
    """
    Buckets poker hands into discrete clusters for CFR.
    
    Preflop: 5 buckets based on hand strength percentiles
    Postflop: 6 buckets based on hand rank and strength
    """
    
    # NO ABSTRACTION: Use exact hands
    PREFLOP_BUCKETS = 1326  # 52*51/2 = 1326 possible 2-card combinations
    
    # Postflop buckets (exact 7-card combinations)
    POSTFLOP_BUCKETS = 2**31  # Large number for exact combinations
    
    @staticmethod
    def get_preflop_bucket(hole_cards: List[int]) -> int:
        """
        NO ABSTRACTION: Use exact hand cards as bucket.
        
        Returns:
            Unique integer for each possible 2-card combination (0 to 1325)
        """
        if len(hole_cards) != 2:
            return 0
        
        c1, c2 = hole_cards[0], hole_cards[1]
        
        # Create unique ID for this exact hand
        # Use canonical ordering (lower card first, then higher)
        if c1 < c2:
            low_card = c1
            high_card = c2
        else:
            low_card = c2
            high_card = c1
        
        # Create unique bucket ID (0 to 1325 for 52*51/2 combinations)
        return low_card * 52 + high_card
    
    @staticmethod
    def get_postflop_bucket(hole_cards: List[int], board: List[int]) -> int:
        """
        Bucket postflop hands into 6 categories based on made hand strength.
        
        Returns:
            0 = air (high card)
            1 = weak pair (pair, weak kicker)
            2 = strong pair (pair, good kicker)
            3 = two pair / weak trips
            4 = strong trips / straight / flush
            5 = full house or better
        """
        if len(board) == 0:
            return CardAbstraction.get_preflop_bucket(hole_cards)
        
        # NO ABSTRACTION: Use exact hand + board combination as bucket
        all_cards = sorted(hole_cards + board)
        
        # Create unique bucket ID using all 7 cards
        bucket_id = 0
        for i, card in enumerate(all_cards):
            bucket_id += card * (52 ** i)
        
        return bucket_id % (2**31)  # Keep it within int32 range
    
    @staticmethod
    def _has_strong_trips(hole_cards: List[int], board: List[int]) -> bool:
        """Check if trips are strong (pocket pair or top card)."""
        ranks = [poker_engine.get_rank(c) for c in hole_cards + board]
        rank_counts = {}
        for r in ranks:
            rank_counts[r] = rank_counts.get(r, 0) + 1
        
        # Find trips rank (if any)
        trips_ranks = [r for r, count in rank_counts.items() if count == 3]
        if not trips_ranks:
            return False  # No trips
        
        trips_rank = max(trips_ranks)
        hole_ranks = [poker_engine.get_rank(c) for c in hole_cards]
        
        # Strong if pocket pair or high rank (J+)
        return (hole_ranks[0] == hole_ranks[1]) or (trips_rank >= 11)
    
    @staticmethod
    def _has_strong_pair(hole_cards: List[int], board: List[int]) -> bool:
        """Check if pair is strong (overpair or top pair good kicker)."""
        hole_ranks = sorted([poker_engine.get_rank(c) for c in hole_cards], reverse=True)
        board_ranks = [poker_engine.get_rank(c) for c in board]
        max_board_rank = max(board_ranks) if board_ranks else 0
        
        # Overpair or pocket pair
        if hole_ranks[0] == hole_ranks[1]:
            return hole_ranks[0] >= max_board_rank
        
        # Top pair with good kicker (A-J)
        if hole_ranks[0] in board_ranks or hole_ranks[1] in board_ranks:
            kicker = max(hole_ranks)
            return kicker >= 11  # Jack or better
        
        return False


class ActionAbstraction:
    """
    Simplified action space for CFR.
    
    Actions:
    - FOLD: Give up the hand
    - CALL: Match current bet
    - BET_HALF: Bet 50% of pot
    - BET_POT: Bet 100% of pot
    """
    
    FOLD = 0
    CALL = 1
    BET_HALF = 2
    BET_POT = 3
    
    ACTION_NAMES = ["FOLD", "CALL", "BET_HALF", "BET_POT"]
    
    @staticmethod
    def get_legal_actions(can_check: bool, to_call: int, num_raises: int = 0, max_raises: int = 3) -> List[int]:
        """
        Return legal actions given the game state.
        
        Args:
            can_check: True if player can check (to_call == 0)
            to_call: Amount needed to call
            num_raises: Number of raises this round
            max_raises: Maximum raises per round
            
        Returns:
            List of legal action indices
        """
        if can_check:
            # Can check or bet (if not at max raises)
            if num_raises < max_raises:
                return [ActionAbstraction.CALL, ActionAbstraction.BET_HALF, ActionAbstraction.BET_POT]
            else:
                return [ActionAbstraction.CALL]  # Can only check
        else:
            # Facing a bet: can fold, call, or raise (if not at max)
            if num_raises < max_raises:
                return [ActionAbstraction.FOLD, ActionAbstraction.CALL, ActionAbstraction.BET_HALF, ActionAbstraction.BET_POT]
            else:
                return [ActionAbstraction.FOLD, ActionAbstraction.CALL]  # No more raises allowed
    
    @staticmethod
    def action_to_bet_size(action: int, pot: int, to_call: int, stack: int) -> float:
        """
        Convert abstract action to actual bet size.
        
        Args:
            action: Abstract action index
            pot: Current pot size
            to_call: Amount needed to call
            stack: Player's remaining stack
            
        Returns:
            Bet size (or 0 for fold/call)
        """
        if action == ActionAbstraction.FOLD:
            return 0.0
        elif action == ActionAbstraction.CALL:
            return 0.0  # Signal to call
        elif action == ActionAbstraction.BET_HALF:
            # Bet/raise to 0.5× pot
            total_pot_after_call = pot + to_call
            bet_amount = total_pot_after_call * 0.5
            return min(bet_amount, stack)
        elif action == ActionAbstraction.BET_POT:
            # Bet/raise to 1.0× pot
            total_pot_after_call = pot + to_call
            bet_amount = total_pot_after_call * 1.0
            return min(bet_amount, stack)
        else:
            return 0.0

