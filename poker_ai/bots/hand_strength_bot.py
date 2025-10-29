import random

class HandStrengthBot:
    """
    Python HandStrengthBot that subclasses C++ Bot interface.
    
    Current thresholds (moderate):
    - raise_threshold = 0.30 
    - call_threshold = 0.15
    - bluff_frequency = 0.05 (5% bluff when marginal)
    """
    
    def __init__(self, seed: int = 12345,
                 raise_threshold: float = 0.30,
                 call_threshold: float = 0.15,
                 bluff_frequency: float = 0.05):
        """
        Initialize hand strength bot.
        
        Args:
            seed: Random seed for bluffing RNG
            raise_threshold: Minimum strength to raise/bet aggressively
            call_threshold: Minimum strength to call
            bluff_frequency: Probability of bluffing with marginal hands
        """
        try:
            from poker_ai import poker_engine
            self._base = poker_engine.Bot
        except ImportError:
            pass
        
        self._rng = random.Random(seed)
        self.raise_threshold = raise_threshold
        self.call_threshold = call_threshold
        self.bluff_frequency = bluff_frequency
        self.name = "HandStrengthBot"
    
    def _compute_strength(self, hole_cards, board) -> float:
        """
        Evaluate 7-card strength using C++ evaluator.
        
        Args:
            hole_cards: Player's 2 hole cards
            board: Community cards (0-5 cards)
        
        Returns:
            Normalized strength in [0,1] where higher = stronger
        """
        from poker_ai import poker_engine
        
        # Build 7-card set
        cards = list(hole_cards) + list(board)
        
        # Preflop: use simple high-card heuristic (evaluator needs 5+ cards)
        if len(cards) < 5:
            # Simple preflop strength: high cards are strong
            ranks = [poker_engine.get_rank(c) for c in hole_cards]
            # Rank 0=2, 12=Ace; normalize to [0,1]
            avg_rank = sum(ranks) / len(ranks) / 12.0
            # Pair bonus
            if len(set(ranks)) == 1:
                avg_rank = min(1.0, avg_rank + 0.3)
            return avg_rank
        
        # Evaluate using C++ evaluator
        score = poker_engine.HandEvaluator.evaluate(cards)
        
        # Map score to [0,1], higher score -> stronger hand
        # Score ranges: ~0 (high card) to ~8M (straight flush)
        # Use inverse mapping for intuitive thresholds
        max_score = 8500000.0  # slightly above straight flush
        s = 1.0 - (max_score - min(float(score), max_score)) / max_score
        return max(0.0, min(1.0, s))
    
    def get_action(self, hole_cards, board, pot, to_call, stack, can_check):
        """
        Make decision based on hand strength and pot odds.
        
        Args:
            hole_cards: Player's 2 hole cards
            board: Community cards
            pot: Current pot size
            to_call: Amount needed to call
            stack: Player's remaining stack
            can_check: Whether checking is allowed
        
        Returns:
            Action enum value
        """
        from poker_ai import poker_engine
        Action = poker_engine.Action
        
        strength = self._compute_strength(hole_cards, board)
        
        if to_call == 0:
            # No bet to call - can check or bet
            if strength >= self.raise_threshold:
                return Action.BET
            # Marginal bluff chance
            if strength >= self.call_threshold or self._rng.random() < self.bluff_frequency:
                return Action.BET
            return Action.CHECK if can_check else Action.FOLD
        else:
            # Need to call, fold, or raise
            # NEW: More aggressive raising with multiple opportunities
            if strength >= self.raise_threshold:
                return Action.RAISE
            # NEW: Call with medium hands, but raise with strong hands
            if strength >= self.call_threshold:
                # If we have a strong hand, sometimes raise instead of just calling
                if strength >= self.raise_threshold * 0.8 and self._rng.random() < 0.3:
                    return Action.RAISE
                return Action.CALL
            return Action.FOLD
    
    def get_bet_size(self, pot, stack):
        """
        Args:
            pot: Current pot size
            stack: Player's remaining stack
        
        Returns:
            Bet size in chips
        """
        bet_sizes = [0.5, 0.75, 1.0, 1.5]
        chosen_size = self._rng.choice(bet_sizes)
        
        bet_amount = max(1, min(int(pot * chosen_size), int(stack)))
        return bet_amount
