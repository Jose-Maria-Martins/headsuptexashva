#!/usr/bin/env python3
"""
Flask UI for Poker AI - MVP
Provides Bot vs Bot and Human vs Bot gameplay visualization.
"""

from flask import Flask, render_template, jsonify, request
import sys
from pathlib import Path
import random
import time
import threading

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

try:
    from poker_ai import poker_engine
    from poker_ai.bots.random_bot import RandomBot
    from poker_ai.bots.hand_strength_bot import HandStrengthBot
    from poker_ai.bots.monte_carlo_bot import MonteCarloBot
    
    ENGINE_AVAILABLE = True
except ImportError:
    ENGINE_AVAILABLE = False

app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

# Game state storage
bot_vs_bot_state = None
human_vs_bot_state = None


class WrappedBot(poker_engine.Bot):
    """Wrapper to make Python bots compatible with C++ engine."""
    def __init__(self, impl):
        super().__init__()
        self._impl = impl
    
    def get_action(self, hole_cards, board, pot, to_call, stack, can_check):
        return self._impl.get_action(hole_cards, board, pot, to_call, stack, can_check)
    
    def get_bet_size(self, pot, stack):
        return self._impl.get_bet_size(pot, stack)


def create_bot(bot_type, seed=0):
    """Create a bot instance based on type string."""
    if bot_type == "v0" or bot_type == "random":
        return WrappedBot(RandomBot(seed))
    elif bot_type == "v1" or bot_type == "handstrength":
        return WrappedBot(HandStrengthBot(seed))
    elif bot_type == "v2" or bot_type == "montecarlo":
        return WrappedBot(MonteCarloBot(seed, rollouts=200))
    else:
        raise ValueError(f"Unknown bot type: {bot_type}")


def card_to_dict(card):
    """Convert card ID to readable format."""
    ranks = ['2','3','4','5','6','7','8','9','10','J','Q','K','A']
    suits = ['♠','♥','♦','♣']
    rank_val = card // 4
    suit_val = card % 4
    return {
        'rank': ranks[rank_val],
        'suit': suits[suit_val],
        'id': card
    }


def hand_to_dicts(hole_cards):
    """Convert hole cards array to list of card dicts."""
    return [card_to_dict(c) for c in hole_cards]


@app.route('/')
def index():
    """Main menu."""
    return render_template('index.html')


@app.route('/bot-vs-bot')
def bot_vs_bot():
    """Bot vs Bot spectator mode."""
    return render_template('bot_vs_bot.html')


@app.route('/play')
def play():
    """Human vs Bot gameplay."""
    return render_template('play.html')


@app.route('/api/bot-vs-bot/start', methods=['POST'])
def bot_vs_bot_start():
    """Start a bot vs bot match."""
    if not ENGINE_AVAILABLE:
        return jsonify({'error': 'Engine not available'}), 500
    
    data = request.json
    bot_a_type = data.get('botA', 'v0')
    bot_b_type = data.get('botB', 'v0')
    hands = data.get('hands', 200)
    
    # Create bots
    bot_a = create_bot(bot_a_type, seed=42)
    bot_b = create_bot(bot_b_type, seed=84)
    
    # Create simulator
    config = poker_engine.SimConfig()
    config.initial_stack = 1000
    config.small_blind = 5
    config.big_blind = 10
    config.seed = int(time.time())
    
    sim = poker_engine.Simulator(config)
    
    # Run the full match immediately
    print(f"Running match: {bot_a_type} vs {bot_b_type} ({hands} hands)")
    result = sim.simulate_match(bot_a, bot_b, hands)
    
    # Store state with full match results
    global bot_vs_bot_state
    bot_vs_bot_state = {
        'sim': sim,
        'bot_a': bot_a,
        'bot_b': bot_b,
        'bot_a_type': bot_a_type,
        'bot_b_type': bot_b_type,
        'hands_to_play': hands,
        'match_result': result,
        'current_hand': 0,
        'running': True
    }
    
    return jsonify({'status': 'completed', 'hands': hands})


@app.route('/api/bot-vs-bot/next')
def bot_vs_bot_next():
    """Get next hand state for bot vs bot."""
    if not bot_vs_bot_state:
        return jsonify({'error': 'No match started'}), 400
    
    result = bot_vs_bot_state['match_result']
    
    # Increment progress
    bot_vs_bot_state['current_hand'] += 10
    
    # Calculate progress percentage
    hands_shown = min(bot_vs_bot_state['current_hand'], result.hands_played)
    progress = hands_shown / result.hands_played if result.hands_played > 0 else 1.0
    finished = bot_vs_bot_state['current_hand'] >= result.hands_played
    
    # Use actual data, not interpolation (interpolation was misleading)
    p0_stack = result.p0_final_stack
    p1_stack = result.p1_final_stack
    p0_wins = result.p0_wins
    p1_wins = result.p1_wins
    
    return jsonify({
        'hand': hands_shown,
        'total_hands': result.hands_played,
        'p0_stack': p0_stack,
        'p1_stack': p1_stack,
        'p0_wins': p0_wins,
        'p1_wins': p1_wins,
        'finished': finished
    })


@app.route('/api/play/start', methods=['POST'])
def play_start():
    """Start a human vs bot match."""
    if not ENGINE_AVAILABLE:
        return jsonify({'error': 'Engine not available'}), 500
    
    data = request.json
    difficulty = data.get('difficulty', 'v0')
    
    # Create bot opponent
    bot_opponent = create_bot(difficulty, seed=123)

    # Create simulator config (we'll run stepwise in Python, not via batch API)
    config = poker_engine.SimConfig()
    config.initial_stack = 1000
    config.small_blind = 10
    config.big_blind = 20
    config.seed = int(time.time())

    # Initialize per-game state for 2 betting rounds: preflop and river
    # We'll manage cards/stacks here and consult bot via WrappedBot
    global human_vs_bot_state
    human_vs_bot_state = {
        'difficulty': difficulty,
        'bot': bot_opponent,
        'config': config,
        'rng': random.Random(config.seed),
        'stacks': [config.initial_stack, config.initial_stack],  # [human, bot]
        'button': 0,  # 0 means human is BB, bot is SB for first hand (matches engine parity)
        'hand_active': False,
        'hand_id': 0,
        'history': [],
        'max_raises': 3,
    }

    return jsonify({'status': 'started'})


def _deal_hole_cards(rng):
    deck = list(range(52))
    rng.shuffle(deck)
    return deck[:2], deck[2:4], deck[4:9]  # human, bot, 5-card board


def _get_rank(card):
    return poker_engine.get_rank(card)


def _get_suit(card):
    return poker_engine.get_suit(card)


def _make_public_state(state):
    """Return UI-friendly snapshot of current game state."""
    human_hole = state.get('human_hole', [])
    # Hide board on preflop
    board = state.get('board', []) if state.get('street') == 'river' else []
    # Reveal bot hole cards only at showdown (after betting ends)
    bot_hole_public = state.get('bot_hole', []) if state.get('hand_over', False) else []
    # Compute to_call dynamically for the human when it's their turn
    if state.get('hand_over', False):
        to_call = 0
    else:
        to_call = _to_call_for(state, 'human') if state.get('turn') == 'human' else 0
    can_check = (to_call == 0)
    # Show pot including chips currently on the table (blinds/bets not yet settled)
    pot_visible = state.get('pot', 0) + sum(state.get('current_bets', [0, 0]))
    return {
        'hand_id': state['hand_id'],
        'street': state.get('street', 'preflop'),
        'stacks': state['stacks'],
        'pot': pot_visible,
        'current_bets': state.get('current_bets', [0, 0]),
        'to_call': to_call,
        'can_check': can_check,
        'can_raise': state.get('raises', 0) < state.get('max_raises', 3),
        'human': hand_to_dicts(human_hole) if human_hole else [],
        'board': [card_to_dict(c) for c in board],
        'bot': hand_to_dicts(bot_hole_public) if bot_hole_public else [],
        'history': state['history'][-8:],
        'your_turn': state.get('turn') == 'human',
        'hand_over': state.get('hand_over', False),
    }


@app.route('/api/play/state', methods=['GET'])
def play_state():
    if not human_vs_bot_state:
        return jsonify({'error': 'Game not started'}), 400
    return jsonify(_make_public_state(human_vs_bot_state))


def _post_blinds(state):
    cfg = state['config']
    stacks = state['stacks']
    # positions: button 0 => human BB, bot SB (to mirror engine rotation)
    if state['button'] == 0:
        sb_pos, bb_pos = 1, 0
    else:
        sb_pos, bb_pos = 0, 1
    sb_amt = min(cfg.small_blind, stacks[sb_pos])
    bb_amt = min(cfg.big_blind, stacks[bb_pos])
    stacks[sb_pos] -= sb_amt
    stacks[bb_pos] -= bb_amt
    state['current_bets'] = [0, 0]
    state['current_bets'][sb_pos] = sb_amt
    state['current_bets'][bb_pos] = bb_amt
    state['pot'] = 0  # will be added after round completes
    state['history'].append(f"Blinds posted SB={sb_amt}, BB={bb_amt}")


def _advance_turn(state):
    state['turn'] = 'bot' if state.get('turn') == 'human' else 'human'


def _betting_complete(state, last_raiser):
    b0, b1 = state['current_bets']
    cur = 0 if state['turn'] == 'human' else 1
    # equalized and no one just raised
    return (b0 == b1) and (last_raiser != cur)


def _apply_call(state, pos, to_call):
    amt = min(to_call, state['stacks'][pos])
    state['current_bets'][pos] += amt
    state['stacks'][pos] -= amt


def _settle_to_pot(state):
    b0, b1 = state['current_bets']
    state['pot'] += b0 + b1
    state['current_bets'] = [0, 0]


def _to_call_for(state, player):
    cur_bets = state['current_bets']
    p = 0 if player == 'human' else 1
    return max(cur_bets[0], cur_bets[1]) - cur_bets[p]


def _bot_step(state):
    """Run a single bot decision; return True if progressed, False if no-op."""
    if state.get('turn') != 'bot' or state.get('hand_over'):
        return False
    tc_bot = _to_call_for(state, 'bot')
    can_check_bot = (tc_bot == 0)
    hole = state['bot_hole']
    board = [] if state['street'] == 'preflop' else state['board']
    pot_for_bot = state['pot'] + sum(state['current_bets'])
    bot_action = state['bot'].get_action(hole, board, pot_for_bot, tc_bot, state['stacks'][1], can_check_bot)

    if bot_action == poker_engine.Action.FOLD:
        _settle_to_pot(state)
        state['stacks'][0] += state['pot']
        state['history'].append("Bot folds.")
        state['hand_over'] = True
        state['pot'] = 0
        return True
    if bot_action == poker_engine.Action.CHECK:
        if tc_bot > 0:
            _settle_to_pot(state)
            state['stacks'][0] += state['pot']
            state['history'].append("Bot invalid check -> fold.")
            state['hand_over'] = True
            state['pot'] = 0
            return True
        # valid check: if equalized, advance street/showdown
        if state['street'] == 'preflop':
            _settle_to_pot(state)
            state['street'] = 'river'
            state['turn'] = 'human'
            state['history'].append("Both checked. Moving to river.")
            return True
        else:
            _settle_to_pot(state)
            human_cards = list(state['human_hole']) + list(state['board'])
            bot_cards = list(state['bot_hole']) + list(state['board'])
            h_score = poker_engine.HandEvaluator.evaluate(human_cards)
            b_score = poker_engine.HandEvaluator.evaluate(bot_cards)
            if h_score > b_score:
                state['stacks'][0] += state['pot']
                state['history'].append("Showdown: You win.")
            elif h_score < b_score:
                state['stacks'][1] += state['pot']
                state['history'].append("Showdown: Bot wins.")
            else:
                state['stacks'][0] += state['pot'] // 2 + (state['pot'] % 2)
                state['stacks'][1] += state['pot'] // 2
                state['history'].append("Showdown: Split pot.")
            state['hand_over'] = True
            state['pot'] = 0
            return True
    if bot_action == poker_engine.Action.CALL:
        _apply_call(state, 1, tc_bot)
        state['history'].append(f"Bot calls {tc_bot}.")
        if state['street'] == 'preflop':
            _settle_to_pot(state)
            state['street'] = 'river'
            state['turn'] = 'human'
            state['history'].append("Preflop equalized. Moving to river.")
        else:
            _settle_to_pot(state)
            human_cards = list(state['human_hole']) + list(state['board'])
            bot_cards = list(state['bot_hole']) + list(state['board'])
            h_score = poker_engine.HandEvaluator.evaluate(human_cards)
            b_score = poker_engine.HandEvaluator.evaluate(bot_cards)
            if h_score > b_score:
                state['stacks'][0] += state['pot']
                state['history'].append("Showdown: You win.")
            elif h_score < b_score:
                state['stacks'][1] += state['pot']
                state['history'].append("Showdown: Bot wins.")
            else:
                state['stacks'][0] += state['pot'] // 2 + (state['pot'] % 2)
                state['stacks'][1] += state['pot'] // 2
                state['history'].append("Showdown: Split pot.")
            state['hand_over'] = True
            state['pot'] = 0
        return True
    # bet/raise
    if state.get('raises', 0) >= state.get('max_raises', 3):
        # Raise cap reached: convert to call/check
        if tc_bot > 0:
            _apply_call(state, 1, tc_bot)
            state['history'].append(f"Bot calls {tc_bot} (raise cap).")
            if state['street'] == 'preflop':
                _settle_to_pot(state)
                state['street'] = 'river'
                state['turn'] = 'human'
                state['history'].append("Preflop equalized. Moving to river.")
            else:
                _settle_to_pot(state)
                human_cards = list(state['human_hole']) + list(state['board'])
                bot_cards = list(state['bot_hole']) + list(state['board'])
                h_score = poker_engine.HandEvaluator.evaluate(human_cards)
                b_score = poker_engine.HandEvaluator.evaluate(bot_cards)
                if h_score > b_score:
                    state['stacks'][0] += state['pot']
                    state['history'].append("Showdown: You win.")
                elif h_score < b_score:
                    state['stacks'][1] += state['pot']
                    state['history'].append("Showdown: Bot wins.")
                else:
                    state['stacks'][0] += state['pot'] // 2 + (state['pot'] % 2)
                    state['stacks'][1] += state['pot'] // 2
                    state['history'].append("Showdown: Split pot.")
                state['hand_over'] = True
                state['pot'] = 0
        else:
            # can check
            if state['street'] == 'preflop':
                _settle_to_pot(state)
                state['street'] = 'river'
                state['turn'] = 'human'
                state['history'].append("Both checked (cap). Moving to river.")
            else:
                _settle_to_pot(state)
                human_cards = list(state['human_hole']) + list(state['board'])
                bot_cards = list(state['bot_hole']) + list(state['board'])
                h_score = poker_engine.HandEvaluator.evaluate(human_cards)
                b_score = poker_engine.HandEvaluator.evaluate(bot_cards)
                if h_score > b_score:
                    state['stacks'][0] += state['pot']
                    state['history'].append("Showdown: You win.")
                elif h_score < b_score:
                    state['stacks'][1] += state['pot']
                    state['history'].append("Showdown: Bot wins.")
                else:
                    state['stacks'][0] += state['pot'] // 2 + (state['pot'] % 2)
                    state['stacks'][1] += state['pot'] // 2
                    state['history'].append("Showdown: Split pot.")
                state['hand_over'] = True
                state['pot'] = 0
        return True
    size = state['bot'].get_bet_size(pot_for_bot, state['stacks'][1])
    if size < 1:
        size = state['config'].big_blind
    min_raise = max(state['config'].big_blind, tc_bot + 1)
    desired_total = max(state['current_bets'][1] + tc_bot + size, state['current_bets'][1] + min_raise)
    addl = min(max(desired_total - state['current_bets'][1], 0), state['stacks'][1])
    if addl <= 0:
        # Could not raise; fallback to call/check
        if tc_bot > 0:
            _apply_call(state, 1, tc_bot)
            state['history'].append(f"Bot calls {tc_bot} (no raise possible).")
        else:
            state['history'].append("Bot checks (no raise possible).")
        # handle street advancement similar to check/call paths
        if state['street'] == 'preflop':
            _settle_to_pot(state)
            state['street'] = 'river'
            state['turn'] = 'human'
            state['history'].append("Preflop equalized. Moving to river.")
        else:
            _settle_to_pot(state)
            human_cards = list(state['human_hole']) + list(state['board'])
            bot_cards = list(state['bot_hole']) + list(state['board'])
            h_score = poker_engine.HandEvaluator.evaluate(human_cards)
            b_score = poker_engine.HandEvaluator.evaluate(bot_cards)
            if h_score > b_score:
                state['stacks'][0] += state['pot']
                state['history'].append("Showdown: You win.")
            elif h_score < b_score:
                state['stacks'][1] += state['pot']
                state['history'].append("Showdown: Bot wins.")
            else:
                state['stacks'][0] += state['pot'] // 2 + (state['pot'] % 2)
                state['stacks'][1] += state['pot'] // 2
                state['history'].append("Showdown: Split pot.")
            state['hand_over'] = True
            state['pot'] = 0
        return True
    state['current_bets'][1] += addl
    state['stacks'][1] -= addl
    state['raises'] = state.get('raises', 0) + 1
    state['history'].append(f"Bot bets/raises to {state['current_bets'][1]}.")
    state['turn'] = 'human'
    return True


@app.route('/api/play/next-hand', methods=['POST'])
def play_next_hand():
    if not human_vs_bot_state:
        return jsonify({'error': 'Game not started'}), 400
    s = human_vs_bot_state
    s['hand_id'] += 1
    s['hand_over'] = False
    s['street'] = 'preflop'
    s['history'].append(f"--- Hand {s['hand_id']} ---")
    # rotate button
    s['button'] = 1 - s['button']
    human, bot, board = _deal_hole_cards(s['rng'])
    s['human_hole'] = human
    s['bot_hole'] = bot
    s['board'] = board
    _post_blinds(s)
    # first to act preflop: SB (position acting first). Determine whose turn.
    # With button rotation above, we mirror engine parity where position 0 acts first.
    s['turn'] = 'human' if (s['button'] == 1) else 'bot'
    s['raises'] = 0
    # If it's bot's turn to start, auto-step until it's your turn or hand ends
    steps = 0
    while s['turn'] == 'bot' and not s.get('hand_over') and steps < 5:
        progressed = _bot_step(s)
        steps += 1
        # If bot checked/called and advanced street/showdown, loop will break appropriately
        if not progressed:
            break
        # If bot bet/raised, _bot_step sets turn to human and we stop
    return jsonify(_make_public_state(s))


@app.route('/api/play/action', methods=['POST'])
def play_action():
    if not human_vs_bot_state:
        return jsonify({'error': 'Game not started'}), 400
    s = human_vs_bot_state
    if s.get('hand_over'):
        return jsonify(_make_public_state(s))

    data = request.json or {}
    action = data.get('action')  # 'fold' | 'call' | 'bet'
    bet_size = int(data.get('size', 0))

    def pos_of(player):
        # human = 0, bot = 1
        return 0 if player == 'human' else 1

    def to_call_for(player):
        return _to_call_for(s, player)

    # Only process when it's human's turn
    if s.get('turn') != 'human':
        return jsonify(_make_public_state(s))

    # Compute to_call and can_check
    tc = to_call_for('human')
    can_check = (tc == 0)

    if action == 'fold':
        _settle_to_pot(s)
        winner = 1  # bot wins
        s['stacks'][winner] += s['pot']
        s['history'].append("You folded.")
        s['hand_over'] = True
        return jsonify(_make_public_state(s))

    if action == 'call':
        _apply_call(s, 0, tc)
        s['history'].append(f"You call {tc}.")
        # If equalized after your call, advance street/showdown immediately
        if s['current_bets'][0] == s['current_bets'][1]:
            if s['street'] == 'preflop':
                _settle_to_pot(s)
                s['street'] = 'river'
                s['turn'] = 'human'
                s['history'].append("Preflop equalized. Moving to river.")
                return jsonify(_make_public_state(s))
            else:
                _settle_to_pot(s)
                human_cards = list(s['human_hole']) + list(s['board'])
                bot_cards = list(s['bot_hole']) + list(s['board'])
                h_score = poker_engine.HandEvaluator.evaluate(human_cards)
                b_score = poker_engine.HandEvaluator.evaluate(bot_cards)
                if h_score > b_score:
                    s['stacks'][0] += s['pot']
                    s['history'].append("Showdown: You win.")
                elif h_score < b_score:
                    s['stacks'][1] += s['pot']
                    s['history'].append("Showdown: Bot wins.")
                else:
                    s['stacks'][0] += s['pot'] // 2 + (s['pot'] % 2)
                    s['stacks'][1] += s['pot'] // 2
                    s['history'].append("Showdown: Split pot.")
                s['hand_over'] = True
                s['pot'] = 0
                return jsonify(_make_public_state(s))
    elif action == 'bet':
        # Validate bet/raise with cap and safety fallbacks
        if s['raises'] >= s['max_raises']:
            # Convert to call/check when cap reached
            if tc > 0:
                _apply_call(s, 0, tc)
                s['history'].append(f"You call {tc} (raise cap).")
            else:
                s['history'].append("You check (raise cap).")
        else:
            # Use big blind as baseline min raise increment
            min_raise = max(s['config'].big_blind, tc + 1)
            bet_total = s['current_bets'][0] + tc + bet_size
            desired_total = max(bet_total, s['current_bets'][0] + min_raise)
            addl = min(max(desired_total - s['current_bets'][0], 0), s['stacks'][0])
            if addl <= 0:
                if tc > 0:
                    _apply_call(s, 0, tc)
                    s['history'].append(f"You call {tc} (no raise possible).")
                else:
                    s['history'].append("You check (no raise possible).")
            else:
                s['current_bets'][0] += addl
                s['stacks'][0] -= addl
                s['raises'] += 1
                s['history'].append(f"You bet/raise to {s['current_bets'][0]}.")

    # After human action, switch turn to bot and run bot until next human turn or hand over
    s['turn'] = 'bot'

    # Bot loop: always allow bot to respond (even at raise cap, it will call/check)
    actions_this_round = 0
    while s.get('turn') == 'bot' and actions_this_round < 20 and not s.get('hand_over'):
        actions_this_round += 1
        progressed = _bot_step(s)
        if not progressed:
            break

    # Fallback: if loop ended without action, resolve equality/advance or hand control back to human
    if not s.get('hand_over'):
        if s['current_bets'][0] == s['current_bets'][1]:
            if s['street'] == 'preflop':
                _settle_to_pot(s)
                s['street'] = 'river'
                s['turn'] = 'human'
                s['history'].append("Preflop equalized. Moving to river.")
            else:
                _settle_to_pot(s)
                human_cards = list(s['human_hole']) + list(s['board'])
                bot_cards = list(s['bot_hole']) + list(s['board'])
                h_score = poker_engine.HandEvaluator.evaluate(human_cards)
                b_score = poker_engine.HandEvaluator.evaluate(bot_cards)
                if h_score > b_score:
                    s['stacks'][0] += s['pot']
                    s['history'].append("Showdown: You win.")
                elif h_score < b_score:
                    s['stacks'][1] += s['pot']
                    s['history'].append("Showdown: Bot wins.")
                else:
                    s['stacks'][0] += s['pot'] // 2 + (s['pot'] % 2)
                    s['stacks'][1] += s['pot'] // 2
                    s['history'].append("Showdown: Split pot.")
                s['hand_over'] = True
                s['pot'] = 0
        else:
            # Not equalized and raise cap hit: pass turn back to human to act
            s['turn'] = 'human'

    return jsonify(_make_public_state(s))


if __name__ == '__main__':
    print("=" * 80)
    print("POKER AI UI - Starting Flask Server")
    print("=" * 80)
    print(f"Engine available: {ENGINE_AVAILABLE}")
    print("Navigate to: http://localhost:5000")
    print("=" * 80)
    
    app.run(debug=True, host='0.0.0.0', port=5000)

