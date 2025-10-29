import random

class RandomBot:
    """
    Python RandomBot that subclasses C++ Bot interface.
    Makes random valid actions with simple pot-based bet sizing.
    """
    
    def __init__(self, seed: int = 12345):
        """        
        Args:
            seed: Random seed for reproducibility
        """
        try:
            from poker_ai import poker_engine
            self._base = poker_engine.Bot
        except ImportError:
            pass
        
        self._rng = random.Random(seed)
        self.name = "RandomBot"
    
    def get_action(self, hole_cards, board, pot, to_call, stack, can_check):
        """
        Make a random valid action.
        
        Args:
            hole_cards: Player's 2 hole cards (array)
            board: Community cards (list, 0-5 cards)
            pot: Current pot size
            to_call: Amount needed to call
            stack: Player's remaining stack
            can_check: Whether checking is allowed
        
        Returns:
            Action enum value
        """
        from poker_ai import poker_engine
        Action = poker_engine.Action
        
        if to_call == 0:
            # Choose between CHECK or BET
            if self._rng.random() < 0.5:
                return Action.CHECK
            return Action.BET
        else:
            # Choose between FOLD, CALL, RAISE
            r = self._rng.random()
            if r < 0.33:
                return Action.FOLD
            elif r < 0.66:
                return Action.CALL
            else:
                return Action.RAISE
    
    def get_bet_size(self, pot, stack):
        """        
        Args:
            pot: Current pot size
            stack: Player's remaining stack
        
        Returns:
            Bet size in chips
        """
        choice = self._rng.randint(0, 2)
        multiplier = 0.5 if choice == 0 else (0.75 if choice == 1 else 1.0)
        bet = int(pot * multiplier)
        return max(1, min(bet, stack))
