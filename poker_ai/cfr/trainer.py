"""
Monte Carlo CFR Trainer for heads-up poker.

Implements external sampling CFR with outcome sampling.
"""

from poker_ai import poker_engine
import numpy as np
import random
from typing import List, Tuple, Optional
from .abstraction import CardAbstraction, ActionAbstraction
from .infoset import InfoSet, InfoSetManager, build_infoset_key


class GameState:
    """
    Simplified poker game state for CFR.
    
    Two-round model: preflop + postflop (all 5 cards at once).
    """
    
    def __init__(
        self,
        stack: int = 1000,
        sb: int = 10,
        bb: int = 20,
        rng: Optional[random.Random] = None,
        cards: Optional[Tuple[List[int], List[int], List[int]]] = None,
    ):
        """Initialize a new hand."""
        self.initial_stack = stack
        self.sb = sb
        self.bb = bb
        self.rng = rng or random.Random()
        
        # Deal cards
        if cards is None:
            deck = list(range(52))
            self.rng.shuffle(deck)
            self.p0_cards = deck[0:2]
            self.p1_cards = deck[2:4]
            self.board = deck[4:9]
        else:
            self.p0_cards, self.p1_cards, self.board = (
                cards[0].copy(),
                cards[1].copy(),
                cards[2].copy(),
            )
        
        # State
        self.round = 0  # 0=preflop, 1=postflop
        self.current_player = 0  # Seat 0 (small blind) acts first preflop
        self.pot = sb + bb
        self.p0_invested = sb
        self.p1_invested = bb
        self.history = ""
        self.is_over = False
        self.num_raises_this_round = 0  # Limit raises to prevent infinite loops
    
    def get_active_board(self) -> List[int]:
        """Return board for current round."""
        return [] if self.round == 0 else self.board
    
    def is_terminal(self) -> bool:
        """Check if hand is over."""
        return self.is_over
    
    def get_current_player(self) -> int:
        """Return the seat that acts next."""
        return self.current_player
    
    def apply_action(self, action: int, bet_size: float):
        """Apply an action and update state."""
        player = self.get_current_player()
        
        if action == ActionAbstraction.FOLD:
            self.history += 'f'
            self.is_over = True
            
        elif action == ActionAbstraction.CALL:
            self.history += 'c'
            # Match opponent's investment
            if player == 0:
                call_amt = self.p1_invested - self.p0_invested
                self.p0_invested += call_amt
                self.pot += call_amt
            else:
                call_amt = self.p0_invested - self.p1_invested
                self.p1_invested += call_amt
                self.pot += call_amt
            
            # MATCH C++ SIMULATOR: After 2 actions (1 per player), round is over
            if len(self.history) >= 2:
                if self.round == 0:
                    # Move to postflop
                    self.round = 1
                    self.history = ""
                    self.current_player = 1  # Big blind acts first postflop
                    self.num_raises_this_round = 0  # Reset for new round
                else:
                    # Postflop complete
                    self.is_over = True
            else:
                self.current_player = 1 - player
                    
        elif action in [ActionAbstraction.BET_HALF, ActionAbstraction.BET_POT]:
            self.history += 'b'
            self.num_raises_this_round += 1
            # Increase investment
            if player == 0:
                self.p0_invested += bet_size
                self.pot += bet_size
            else:
                self.p1_invested += bet_size
                self.pot += bet_size
            self.current_player = 1 - player
    
    def get_payoff(self, player: int) -> float:
        """
        Calculate payoff for player (profit/loss).
        """
        if self.history.endswith('f'):
            # Fold: last to act folded
            folder = (len(self.history) - 1) % 2
            winner = 1 - folder
            if player == winner:
                return (self.pot / 2)  # Profit
            else:
                return -(self.pot / 2)  # Loss
        
        # Showdown
        p0_score = poker_engine.HandEvaluator.evaluate(self.p0_cards + self.get_active_board())
        p1_score = poker_engine.HandEvaluator.evaluate(self.p1_cards + self.get_active_board())
        
        if p0_score > p1_score:
            winner = 0
        elif p1_score > p0_score:
            winner = 1
        else:
            return 0.0  # Tie
        
        if player == winner:
            return (self.pot / 2)
        else:
            return -(self.pot / 2)


class MCCFRTrainer:
    """
    Monte Carlo Counterfactual Regret Minimization trainer.
    
    Uses external sampling (outcome sampling variant) for efficiency.
    """
    
    def __init__(
        self,
        stack: int = 1000,
        sb: int = 10,
        bb: int = 20,
        seed: int = 12345,
    ):
        """
        Initialize CFR trainer.
        
        Args:
            stack: Starting stack
            sb: Small blind
            bb: Big blind
        """
        self.stack = stack
        self.sb = sb
        self.bb = bb
        self.rng = random.Random(seed)
        
        self.infoset_manager = InfoSetManager()
        self.iteration = 0
    
    def train(self, num_iterations: int, verbose: bool = True):
        """
        Run CFR training for specified iterations.
        
        Args:
            num_iterations: Number of training iterations
            verbose: Print progress
        """
        for i in range(num_iterations):
            self.iteration += 1
            
            # Create new random game
            state = GameState(self.stack, self.sb, self.bb, rng=self.rng)
            
            # Traverse for both players
            for player in [0, 1]:
                self._cfr(state, player, 1.0, 1.0)
            
            if verbose and (i + 1) % 5000 == 0:
                print(f"Iteration {i + 1}/{num_iterations} - InfoSets: {self.infoset_manager.get_num_infosets()}")
    
    def _cfr(self, state: GameState, traverser: int, p0_prob: float, p1_prob: float) -> float:
        """
        Recursive CFR algorithm.
        
        Args:
            state: Current game state
            traverser: Player we're computing regrets for
            p0_prob: Probability player 0 reaches this state
            p1_prob: Probability player 1 reaches this state
            
        Returns:
            Expected value for traverser
        """
        # Terminal state
        if state.is_terminal():
            return state.get_payoff(traverser)
        
        # Get current player
        player = state.get_current_player()
        
        # Get hole cards and board
        hole_cards = state.p0_cards if player == 0 else state.p1_cards
        board = state.get_active_board()
        
        # Get card bucket
        if state.round == 0:
            bucket = CardAbstraction.get_preflop_bucket(hole_cards)
        else:
            bucket = CardAbstraction.get_postflop_bucket(hole_cards, board)
        
        # Build infoset key
        infoset_key = build_infoset_key(bucket, state.round, state.history, player)
        
        # Get legal actions - MATCH C++ SIMULATOR: 1 action per player, no raises
        to_call = (state.p1_invested - state.p0_invested) if player == 0 else (state.p0_invested - state.p1_invested)
        legal_actions = ActionAbstraction.get_legal_actions(to_call == 0, to_call, 0, 0)  # 0 max raises = 1 action per player
        
        # Get or create infoset
        infoset = self.infoset_manager.get_infoset(infoset_key, 4)  # Max 4 actions
        
        # Get current strategy
        if player == traverser:
            strategy = infoset.get_strategy(p0_prob if player == 0 else p1_prob)
        else:
            strategy = infoset.get_strategy(1.0)
        
        # Ensure strategy sums to 1 over legal actions
        legal_strategy = np.zeros(4)
        for a in legal_actions:
            legal_strategy[a] = strategy[a]
        
        # Normalize
        total = np.sum(legal_strategy)
        if total > 0:
            legal_strategy /= total
        else:
            # Uniform over legal actions
            for a in legal_actions:
                legal_strategy[a] = 1.0 / len(legal_actions)
        
        # Expected value for each action
        action_values = np.zeros(4)
        
        # Recurse for each action
        for action in legal_actions:
            # Create copy of state
            new_state = self._copy_state(state)
            
            # Get bet size (use large stack for abstraction)
            bet_size = ActionAbstraction.action_to_bet_size(
                action, new_state.pot, to_call, 10000  # Large stack
            )
            
            # Apply action
            new_state.apply_action(action, bet_size)
            
            # Update probabilities
            if player == 0:
                new_p0_prob = p0_prob * legal_strategy[action]
                new_p1_prob = p1_prob
            else:
                new_p0_prob = p0_prob
                new_p1_prob = p1_prob * legal_strategy[action]
            
            # Recurse
            action_values[action] = self._cfr(new_state, traverser, new_p0_prob, new_p1_prob)
        
        # Expected value
        ev = np.sum(legal_strategy * action_values)
        
        # Update regrets if this is the traverser
        if player == traverser:
            for action in legal_actions:
                regret = action_values[action] - ev
                infoset.add_regret(action, regret)
        
        return ev
    
    def _copy_state(self, state: GameState) -> GameState:
        """Create a copy of game state."""
        new_state = GameState(
            self.stack,
            self.sb,
            self.bb,
            rng=self.rng,
            cards=(state.p0_cards, state.p1_cards, state.board),
        )
        new_state.round = state.round
        new_state.current_player = state.current_player
        new_state.pot = state.pot
        new_state.p0_invested = state.p0_invested
        new_state.p1_invested = state.p1_invested
        new_state.history = state.history
        new_state.is_over = state.is_over
        new_state.num_raises_this_round = state.num_raises_this_round
        return new_state
    
    def _train_against_v2(self, v2_opponent):
        """Train one iteration against V2 opponent instead of self-play."""
        # Create a new game state
        state = GameState(self.stack, self.sb, self.bb, rng=self.rng)
        
        # Play the hand against V2
        self._play_hand_against_v2(state, v2_opponent)
    
    def _play_hand_against_v2(self, state: GameState, v2_opponent):
        """Play one hand against V2 opponent."""
        # Preflop round
        if not state.is_terminal():
            self._play_round_against_v2(state, 0, v2_opponent)  # Player 0 (CFR)
            self._play_round_against_v2(state, 1, v2_opponent)  # Player 1 (V2)
        
        # Postflop round
        if not state.is_terminal():
            state.round = 1
            state.history = ""
            state.num_raises_this_round = 0
            self._play_round_against_v2(state, 0, v2_opponent)  # Player 0 (CFR)
            self._play_round_against_v2(state, 1, v2_opponent)  # Player 1 (V2)
    
    def _play_round_against_v2(self, state: GameState, player: int, v2_opponent):
        """Play one betting round against V2."""
        if state.is_terminal():
            return
        
        # Get legal actions
        to_call = (state.p1_invested - state.p0_invested) if player == 0 else (state.p0_invested - state.p1_invested)
        legal_actions = ActionAbstraction.get_legal_actions(to_call == 0, to_call, 0, 0)
        
        if player == 0:
            # CFR player - use CFR strategy
            action = self._get_cfr_action(state, player, legal_actions)
        else:
            # V2 opponent - use V2 strategy
            action = self._get_v2_action(state, player, v2_opponent, to_call)
        
        # Apply action
        self._apply_action(state, action, player)
    
    def _get_cfr_action(self, state: GameState, player: int, legal_actions: List[int]):
        """Get action using CFR strategy."""
        # Get infoset
        hole_cards = state.p0_cards if player == 0 else state.p1_cards
        board = state.get_active_board()
        
        if state.round == 0:
            bucket = CardAbstraction.get_preflop_bucket(hole_cards)
        else:
            bucket = CardAbstraction.get_postflop_bucket(hole_cards, board)
        
        infoset_key = build_infoset_key(bucket, state.round, state.history, player)
        infoset = self.infoset_manager.get_infoset(infoset_key, len(legal_actions))
        
        # Get strategy
        strategy = infoset.get_strategy()
        
        # Sample action
        return self.rng.choices(legal_actions, weights=strategy, k=1)[0]
    
    def _get_v2_action(self, state: GameState, player: int, v2_opponent, to_call: int):
        """Get action using V2 strategy."""
        hole_cards = state.p0_cards if player == 0 else state.p1_cards
        board = state.get_active_board()
        pot = state.pot
        stack = self.stack - (state.p0_invested if player == 0 else state.p1_invested)
        can_check = (to_call == 0)
        
        # Convert V2 action to our action format
        v2_action = v2_opponent.get_action(hole_cards, board, pot, to_call, stack, can_check)
        
        # Map V2 actions to our action format
        if v2_action == poker_engine.Action.FOLD:
            return ActionAbstraction.FOLD
        elif v2_action == poker_engine.Action.CALL:
            return ActionAbstraction.CALL
        elif v2_action == poker_engine.Action.CHECK:
            return ActionAbstraction.CALL  # Check = Call when no bet
        elif v2_action in [poker_engine.Action.BET, poker_engine.Action.RAISE]:
            return ActionAbstraction.BET_POT  # Use pot-sized bet
        else:
            return ActionAbstraction.CALL
    
    def _apply_action(self, state: GameState, action: int, player: int):
        """Apply action to game state."""
        if action == ActionAbstraction.FOLD:
            state.is_over = True
        elif action == ActionAbstraction.CALL:
            # Call the current bet
            to_call = (state.p1_invested - state.p0_invested) if player == 0 else (state.p0_invested - state.p1_invested)
            if player == 0:
                state.p0_invested += to_call
            else:
                state.p1_invested += to_call
            state.history += 'c'
        elif action in [ActionAbstraction.BET_HALF, ActionAbstraction.BET_POT]:
            # Bet/raise
            bet_size = int(state.pot * (0.5 if action == ActionAbstraction.BET_HALF else 1.0))
            if player == 0:
                state.p0_invested += bet_size
            else:
                state.p1_invested += bet_size
            state.history += 'b'
            state.num_raises_this_round += 1
        
        # Check if betting is complete (both players have equal bets)
        if state.p0_invested == state.p1_invested and len(state.history) >= 2:
            if state.round == 0:
                # Move to postflop
                state.round = 1
                state.history = ""
                state.num_raises_this_round = 0
            else:
                # Postflop complete
                state.is_over = True

    def save_strategy(self, filepath: str):
        """Save trained strategy to file."""
        self.infoset_manager.save(filepath)
        print(f"Saved strategy with {self.infoset_manager.get_num_infosets()} infosets to {filepath}")
    
    def load_strategy(self, filepath: str):
        """Load trained strategy from file."""
        self.infoset_manager.load(filepath)
        print(f"Loaded strategy with {self.infoset_manager.get_num_infosets()} infosets from {filepath}")
