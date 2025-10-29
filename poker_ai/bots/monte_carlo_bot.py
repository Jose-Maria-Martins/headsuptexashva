import random
import math
from typing import List, Tuple, Optional
from poker_ai import poker_engine

class MonteCarloBot:
    """
    V2 Bot with Monte Carlo equity estimation, pot odds, and stack-aware aggression.
    
    Features:
    - Monte Carlo rollouts for postflop equity estimation
    - Pot odds integration for call/fold decisions
    - Stack-aware aggression (more aggressive when ahead, conservative when behind)
    - Semi-bluffing with draw detection
    - Position-aware adjustments
    """
    
    def __init__(self, 
                 seed: int = 12345,
                 rollouts: int = 300,
                 base_call_margin: float = 0.05,
                 base_raise_margin: float = 0.08,
                 aggression_k1: float = 0.05, 
                 aggression_k2: float = 0.02, 
                 semi_bluff_freq: float = 0.25,
                 position_adjustment: float = 0.02,
                 preflop_raise_threshold: float = 0.30,
                 preflop_call_threshold: float = 0.15,
                 opponent_tightness: float = 0.5,  
                 board_texture_awareness: bool = True):
        """
        Initialize Monte Carlo bot.
        
        Args:
            seed: Random seed for reproducibility
            rollouts: Number of Monte Carlo samples for equity estimation
            base_call_margin: Base margin for calling (equity must exceed price + margin)
            base_raise_margin: Base margin for raising
            aggression_k1: Coefficient for stack lead effect on aggression
            aggression_k2: Coefficient for pot pressure effect on aggression
            semi_bluff_freq: Frequency of semi-bluffing when draw detected
            position_adjustment: Threshold adjustment for position (acting last)
            preflop_raise_threshold: Preflop raise threshold (reuse V1 logic)
            preflop_call_threshold: Preflop call threshold (reuse V1 logic)
            opponent_tightness: 0 = loose (be more selective), 1 = tight (be more aggressive). 
        """
        self.rng = random.Random(seed)
        self.rollouts = rollouts
        self.base_call_margin = base_call_margin
        self.base_raise_margin = base_raise_margin
        self.aggression_k1 = aggression_k1
        self.aggression_k2 = aggression_k2
        self.semi_bluff_freq = semi_bluff_freq
        self.position_adjustment = position_adjustment
        self.preflop_raise_threshold = preflop_raise_threshold
        self.preflop_call_threshold = preflop_call_threshold
        self.opponent_tightness = opponent_tightness
        self.board_texture_awareness = board_texture_awareness
        # Cache the last computed equity for sizing decisions
        self._last_equity: Optional[float] = None
        self.name = "MonteCarloBot"
        
        self._equity_cache = {}
        
        # Opponent modeling
        self._opponent_fold_rate = 0.5
        self._opponent_call_rate = 0.3
        self._opponent_raise_rate = 0.2
        
    def _compute_preflop_strength(self, hole_cards) -> float:
        """Compute preflop strength using V1 heuristic."""
        ranks = [poker_engine.get_rank(c) for c in hole_cards]
        avg_rank = sum(ranks) / len(ranks) / 12.0
        if len(set(ranks)) == 1:  # Pair
            avg_rank = min(1.0, avg_rank + 0.3)
        return avg_rank
    
    def _monte_carlo_equity(self, hole_cards, board, initial_stack: int) -> float:
        """
        Estimate equity using Monte Carlo rollouts.
        
        Args:
            hole_cards: Our 2 hole cards
            board: Community cards (0-5)
            initial_stack: Starting stack size for context
            
        Returns:
            Equity estimate [0, 1] where 1 = always win
        """
        cache_key = (tuple(hole_cards), tuple(board))
        if cache_key in self._equity_cache:
            return self._equity_cache[cache_key]
        
        # If preflop through turn, use heuristic for speed
        if len(board) < 5:
            equity = self._compute_preflop_strength(hole_cards)
            self._equity_cache[cache_key] = equity
            return equity
        
        # River only: Monte Carlo rollouts
        wins = 0
        ties = 0
        total_rollouts = 0
        
        known_cards = set(hole_cards) | set(board)
        
        for _ in range(self.rollouts):
            # Generate random opponent hole cards
            opponent_cards = self._generate_opponent_cards(known_cards)
            
            # Evaluate both hands
            our_cards = list(hole_cards) + list(board)
            opp_cards = list(opponent_cards) + list(board)
            
            our_score = poker_engine.HandEvaluator.evaluate(our_cards)
            opp_score = poker_engine.HandEvaluator.evaluate(opp_cards)
            
            if our_score > opp_score:
                wins += 1
            elif our_score == opp_score:
                ties += 1
            total_rollouts += 1
        
        equity = (wins + ties / 2) / total_rollouts if total_rollouts > 0 else 0.0
        self._equity_cache[cache_key] = equity
        return equity
    
    def _generate_opponent_cards(self, known_cards) -> Tuple[int, int]:
        """Generate random opponent hole cards avoiding known cards."""
        available_cards = [c for c in range(52) if c not in known_cards]
        
        if len(available_cards) < 2:
            return (0, 1)
        
        selected = self.rng.sample(available_cards, 2)
        return (selected[0], selected[1])
    
    def _detect_draw(self, hole_cards, board) -> Tuple[bool, str, float]:
        """
        Detect draws and return (has_draw, draw_type, draw_strength).
        
        Returns:
            has_draw: Whether we have any draw
            draw_type: Type of draw ("flush", "straight", "combo", "none")
            draw_strength: Strength of draw [0, 1] where 1 = nut draw
        """
        if len(board) < 3:
            return False, "none", 0.0
        
        all_cards = list(hole_cards) + list(board)
        
        # Check for flush draws
        suits = [poker_engine.get_suit(c) for c in all_cards]
        suit_counts = {}
        for suit in suits:
            suit_counts[suit] = suit_counts.get(suit, 0) + 1
        
        flush_draw = False
        flush_strength = 0.0
        max_suit_count = max(suit_counts.values())
        if max_suit_count >= 4:
            flush_draw = True
            # Check if it's a nut flush draw (ace or king high)
            flush_suit = max(suit_counts, key=suit_counts.get)
            flush_ranks = [poker_engine.get_rank(c) for c in all_cards 
                          if poker_engine.get_suit(c) == flush_suit]
            max_flush_rank = max(flush_ranks)
            flush_strength = max_flush_rank / 12.0  # Normalize to [0, 1]
        
        # Check for straight draws
        ranks = [poker_engine.get_rank(c) for c in all_cards]
        unique_ranks = sorted(set(ranks))
        
        straight_draw = False
        straight_strength = 0.0
        # Check for 4+ consecutive ranks
        for i in range(len(unique_ranks) - 3):
            if unique_ranks[i+3] - unique_ranks[i] <= 4:
                straight_draw = True
                # Strength based on highest card in sequence
                straight_strength = unique_ranks[i+3] / 12.0
                break
        
        # Determine draw type and strength
        if flush_draw and straight_draw:
            return True, "combo", max(flush_strength, straight_strength)
        elif flush_draw:
            return True, "flush", flush_strength
        elif straight_draw:
            return True, "straight", straight_strength
        else:
            return False, "none", 0.0
    
    def _analyze_board_texture(self, board) -> Tuple[str, float]:
        """
        Analyze board texture and return (texture_type, wetness).
        
        Returns:
            texture_type: "dry", "wet", "paired", "coordinated"
            wetness: 0-1 scale where 1 = very wet board
        """
        if len(board) < 3:
            return "dry", 0.0
        
        # Check for paired board
        ranks = [poker_engine.get_rank(c) for c in board]
        rank_counts = {}
        for rank in ranks:
            rank_counts[rank] = rank_counts.get(rank, 0) + 1
        
        if max(rank_counts.values()) >= 2:
            return "paired", 0.8
        
        # Check for flush potential
        suits = [poker_engine.get_suit(c) for c in board]
        suit_counts = {}
        for suit in suits:
            suit_counts[suit] = suit_counts.get(suit, 0) + 1
        
        max_suit_count = max(suit_counts.values())
        flush_potential = max_suit_count / len(board)
        
        # Check for straight potential
        unique_ranks = sorted(set(ranks))
        straight_potential = 0.0
        if len(unique_ranks) >= 3:
            for i in range(len(unique_ranks) - 2):
                if unique_ranks[i+2] - unique_ranks[i] <= 4:
                    straight_potential = 0.6
                    break
        
        # Check for coordination (high cards)
        high_cards = sum(1 for r in ranks if r >= 10)  # T, J, Q, K, A
        coordination = high_cards / len(board)
        
        wetness = (flush_potential + straight_potential + coordination) / 3
        
        if wetness >= 0.7:
            return "wet", wetness
        elif coordination >= 0.6:
            return "coordinated", wetness
        else:
            return "dry", wetness
    
    def _adjust_thresholds_for_opponent(self, base_call_margin: float, 
                                      base_raise_margin: float) -> Tuple[float, float]:
        """Adjust thresholds based on opponent tightness."""

        tightness_factor = 1.0 - self.opponent_tightness  
        
        call_adjustment = tightness_factor * 0.02  
        raise_adjustment = tightness_factor * 0.03 
        
        return (base_call_margin - call_adjustment, 
                base_raise_margin - raise_adjustment)
    
    def _compute_aggression_multiplier(self, stack: int, initial_stack: int, 
                                     to_call: int, pot: int) -> float:
        """Compute aggression multiplier based on stack position and pot pressure."""
        stack_lead_ratio = (stack - initial_stack) / initial_stack
        pot_pressure = to_call / max(1, pot) if pot > 0 else 0
        
        # Aggression increases when ahead, decreases when behind
        # Also decreases with high pot pressure (facing big bets)
        aggression = (self.aggression_k1 * stack_lead_ratio - 
                     self.aggression_k2 * pot_pressure)
        
        return max(-0.1, min(0.2, aggression))
    
    def _get_bet_size(self, equity: float, pot: int, stack: int, 
                     aggression_multiplier: float) -> int:
        """Choose bet size based on equity and aggression."""

        if equity >= 0.8:
            base_size = pot  # 100% pot for strong hands
        elif equity >= 0.6:
            base_size = int(pot * 0.75) 
        elif equity >= 0.4:
            base_size = int(pot * 0.5)   
        else:
            base_size = int(pot * 0.25)
        
        # Adjust by aggression
        size_multiplier = 1.0 + aggression_multiplier
        adjusted_size = int(base_size * size_multiplier)
        
        # never bet more than 80% of stack
        max_bet = int(stack * 0.8)
        return min(adjusted_size, max_bet, pot)
    
    def get_action(self, hole_cards, board, pot, to_call, stack, can_check):
        """        
        Args:
            hole_cards: Our 2 hole cards
            board: Community cards (0-5)
            pot: Current pot size
            to_call: Amount needed to call (0 if can check)
            stack: Our remaining stack
            can_check: Whether we can check (to_call == 0)
            
        Returns:
            Action enum value
        """
        initial_stack = 1000
        
        # Clear equity cache at start of new hand (detected by empty board = preflop)
        # This prevents stale equity from previous hands
        if len(board) == 0:
            self._equity_cache.clear()
        
        # Compute equity
        equity = self._monte_carlo_equity(hole_cards, board, initial_stack)
        
        # Position adjustment (acting last gets slight advantage)
        position_bonus = self.position_adjustment if can_check else 0
        adjusted_equity = equity + position_bonus
        # Remember for bet sizing
        self._last_equity = max(0.0, min(1.0, adjusted_equity))
        
        if to_call > 0:
            # Facing a bet: use pot odds with safety floors
            price = to_call / (pot + to_call) if pot > 0 else 0
            
            # Compute aggression multiplier
            aggression_mult = self._compute_aggression_multiplier(
                stack, initial_stack, to_call, pot)
            
            # Adjust thresholds for opponent and board texture
            call_margin, raise_margin = self._adjust_thresholds_for_opponent(
                self.base_call_margin, self.base_raise_margin)
            
            # Apply aggression multiplier
            call_margin += aggression_mult
            raise_margin += aggression_mult
            
            # Board texture adjustments
            if self.board_texture_awareness:
                texture_type, wetness = self._analyze_board_texture(board)
                if texture_type == "wet" or texture_type == "paired":
                    # Be more selective on wet boards
                    call_margin += 0.02
                    raise_margin += 0.03
                elif texture_type == "dry":
                    # Be more aggressive on dry boards
                    call_margin -= 0.01
                    raise_margin -= 0.02
            
            # Decision logic - pot odds based
            raise_threshold = price + raise_margin
            call_threshold = price + call_margin
            
            if adjusted_equity >= raise_threshold:
                return poker_engine.Action.RAISE
            elif adjusted_equity >= call_threshold:
                return poker_engine.Action.CALL
            else:
                # Randomness guard: small chance to call when close
                if (adjusted_equity >= call_threshold - 0.02 and 
                    self.rng.random() < 0.02):
                    return poker_engine.Action.CALL
                return poker_engine.Action.FOLD
        
        else:
            # Can check or bet - balanced approach
            # Bet with good hands, check marginal hands
            
            # Check for draws and semi-bluff
            has_draw, draw_type, draw_strength = self._detect_draw(hole_cards, board)
            
            # Bet with 60%+ equity (above-average hands)
            if adjusted_equity >= 0.60:
                return poker_engine.Action.BET
            elif (has_draw and adjusted_equity >= 0.30 and 
                  self.rng.random() < self.semi_bluff_freq * draw_strength):
                # Semi-bluff with draws
                return poker_engine.Action.BET
            else:
                return poker_engine.Action.CHECK
    
    def get_bet_size(self, pot, stack):
        """Get bet size using equity-based sizing."""
        equity = self._last_equity if self._last_equity is not None else 0.6
        
        if equity >= 0.80:
            desired = pot  # 100% pot for very strong value
        elif equity >= 0.60:
            desired = int(pot * 0.75)
        elif equity >= 0.40:
            desired = int(pot * 0.50)
        else:
            desired = max(1, int(pot * 0.25))

        max_bet = int(stack * 0.8)
        return max(1, min(desired, max_bet, pot))
