#include "simulator.h"
#include <algorithm>
#include <stdexcept>
#include <cstdio>

namespace poker {

// C++ bot implementations removed - bots are now implemented in Python

// Simulator implementation
Simulator::Simulator(const SimConfig& config)
    : config_(config), rng_(config.seed) {}

void Simulator::deal_hand(
    std::array<Card, 2>& p0_cards,
    std::array<Card, 2>& p1_cards,
    std::vector<Card>& board
) {
    std::vector<Card> deck;
    deck.reserve(52);
    for (Card c = 0; c < 52; ++c) {
        deck.push_back(c);
    }
    std::shuffle(deck.begin(), deck.end(), rng_);

    p0_cards[0] = deck[0];
    p0_cards[1] = deck[1];
    p1_cards[0] = deck[2];
    p1_cards[1] = deck[3];
    board.assign(deck.begin() + 4, deck.begin() + 9);
}

void Simulator::return_uncalled_bets(
    std::array<int, 2>& current_bets,
    std::array<int, 2>& stacks
) {
    if (current_bets[0] == current_bets[1]) {
        return;
    }
    const int matched = std::min(current_bets[0], current_bets[1]);
    if (current_bets[0] > matched) {
        stacks[0] += current_bets[0] - matched;
        current_bets[0] = matched;
    }
    if (current_bets[1] > matched) {
        stacks[1] += current_bets[1] - matched;
        current_bets[1] = matched;
    }
}

int Simulator::resolve_showdown(
    const std::array<Card, 2>& p0_cards,
    const std::array<Card, 2>& p1_cards,
    const std::vector<Card>& board
) {
    // Build 7-card hands
    std::vector<Card> p0_hand = {p0_cards[0], p0_cards[1]};
    p0_hand.insert(p0_hand.end(), board.begin(), board.end());
    
    std::vector<Card> p1_hand = {p1_cards[0], p1_cards[1]};
    p1_hand.insert(p1_hand.end(), board.begin(), board.end());
    
    // Evaluate
    uint32_t p0_score = HandEvaluator::evaluate(p0_hand);
    uint32_t p1_score = HandEvaluator::evaluate(p1_hand);
    
    if (p0_score > p1_score) return 0;
    if (p1_score > p0_score) return 1;
    return -1; // Tie
}

int Simulator::simulate_betting_round(
    Bot* bot0,
    Bot* bot1,
    const std::array<Card, 2>& p0_cards,
    const std::array<Card, 2>& p1_cards,
    const std::vector<Card>& board,
    int& pot,
    std::array<int, 2>& stacks,
    std::array<int, 2>& current_bets,
    HandResult& hand_log,
    int first_to_act
) {
    int current_player = first_to_act;
    int last_raiser = -1;
    int raise_count = 0;
    const int max_raises = config_.max_raises_per_round;
    int actions_this_round = 0;

    auto both_all_in = [&]() {
        return stacks[0] == 0 && stacks[1] == 0;
    };

    auto player_all_in = [&](int player) {
        return stacks[player] == 0;
    };

    while (raise_count < max_raises && actions_this_round < 20) {
        int to_call = std::max(current_bets[0], current_bets[1]) - current_bets[current_player];
        bool can_check = (to_call == 0);

        Action action;
        if (current_player == 0) {
            action = bot0->get_action(p0_cards, board, pot, to_call, stacks[0], can_check);
            hand_log.p0_actions.push_back(action);
        } else {
            action = bot1->get_action(p1_cards, board, pot, to_call, stacks[1], can_check);
            hand_log.p1_actions.push_back(action);
        }

        actions_this_round++;

        if (action == Action::FOLD) {
            return_uncalled_bets(current_bets, stacks);
            pot += current_bets[0] + current_bets[1];
            return 1 - current_player;
        }
        if (action == Action::CHECK) {
            if (to_call > 0) {
                return_uncalled_bets(current_bets, stacks);
                pot += current_bets[0] + current_bets[1];
                return 1 - current_player;
            }
        } else if (action == Action::CALL) {
            int call_amount = std::min(to_call, stacks[current_player]);
            current_bets[current_player] += call_amount;
            stacks[current_player] -= call_amount;
        } else if (action == Action::BET || action == Action::RAISE) {
            if (raise_count >= max_raises) {
                if (to_call > 0) {
                    int call_amount = std::min(to_call, stacks[current_player]);
                    current_bets[current_player] += call_amount;
                    stacks[current_player] -= call_amount;
                }
            } else {
                int bet_size = (current_player == 0) ?
                    bot0->get_bet_size(pot, stacks[0]) :
                    bot1->get_bet_size(pot, stacks[1]);

                int min_raise = std::max(config_.big_blind, to_call + 1);
                int desired_total = std::max(
                    current_bets[current_player] + to_call + bet_size,
                    current_bets[current_player] + min_raise
                );

                int additional_amount = std::min(
                    desired_total - current_bets[current_player],
                    stacks[current_player]
                );

                current_bets[current_player] += additional_amount;
                stacks[current_player] -= additional_amount;
                last_raiser = current_player;
                raise_count++;
            }
        }

        return_uncalled_bets(current_bets, stacks);

        if (both_all_in()) {
            break;
        }

        if (current_bets[0] == current_bets[1] && last_raiser != current_player) {
            break;
        }

        if (player_all_in(current_player) && player_all_in(1 - current_player)) {
            break;
        }

        if (player_all_in(current_player) && current_bets[0] == current_bets[1]) {
            break;
        }

        current_player = 1 - current_player;
    }

    return_uncalled_bets(current_bets, stacks);
    pot += current_bets[0] + current_bets[1];
    current_bets[0] = 0;
    current_bets[1] = 0;

    return -1;
}

HandResult Simulator::simulate_hand(
    Bot* bot0,
    Bot* bot1,
    std::array<int, 2>& stacks,
    int button
) {
    HandResult result;
    result.hands_played = 1;
    result.winner = -1;
    
    // Post blinds
    // The positions have already been swapped in simulate_match() based on button
    // So position 0 ALWAYS posts SB, position 1 ALWAYS posts BB
    // This is consistent across all hands
    
    // Post blinds with short-stack protection
    int sb_amount = std::min(config_.small_blind, stacks[0]);
    int bb_amount = std::min(config_.big_blind, stacks[1]);
    
    stacks[0] -= sb_amount;
    stacks[1] -= bb_amount;
    
    // Start pot at 0 - blinds will be added via current_bets
    int pot = 0;
    std::array<int, 2> current_bets = {
        sb_amount,  // Position 0 posts SB
        bb_amount   // Position 1 posts BB
    };
    
    // Deal hole cards and board from one shuffled deck
    std::array<Card, 2> p0_cards, p1_cards;
    std::vector<Card> board;
    deal_hand(p0_cards, p1_cards, board);
    result.p0_hole = p0_cards;
    result.p1_hole = p1_cards;
    result.board = board;

    // Pre-flop: seat 0 (SB) acts first
    int preflop_action = simulate_betting_round(
        bot0, bot1, p0_cards, p1_cards,
        std::vector<Card>(), pot, stacks, current_bets, result, 0
    );
    if (preflop_action != -1) {
        // Someone folded
        result.winner = preflop_action;
        if (preflop_action == 0) {
            stacks[0] += pot;
        } else {
            stacks[1] += pot;
        }
        result.pot_size = pot;
        return result;
    }
    
    // Post-flop: seat 1 (BB) acts first
    int postflop_action = simulate_betting_round(
        bot0, bot1, p0_cards, p1_cards,
        board, pot, stacks, current_bets, result, 1
    );
    if (postflop_action != -1) {
        // Someone folded
        result.winner = postflop_action;
        if (postflop_action == 0) {
            stacks[0] += pot;
        } else {
            stacks[1] += pot;
        }
        result.pot_size = pot;
        return result;
    }
    
    // Go to showdown
    int winner = resolve_showdown(p0_cards, p1_cards, board);
    // record showdown hand ranks for optional metrics
    {
        std::vector<Card> p0_hand = {p0_cards[0], p0_cards[1]};
        p0_hand.insert(p0_hand.end(), board.begin(), board.end());
        std::vector<Card> p1_hand = {p1_cards[0], p1_cards[1]};
        p1_hand.insert(p1_hand.end(), board.begin(), board.end());
        uint32_t p0_score = HandEvaluator::evaluate(p0_hand);
        uint32_t p1_score = HandEvaluator::evaluate(p1_hand);
        result.p0_showdown_rank = static_cast<int>(HandEvaluator::get_hand_rank(p0_score));
        result.p1_showdown_rank = static_cast<int>(HandEvaluator::get_hand_rank(p1_score));
    }
    
    if (winner == 0) {
        stacks[0] += pot;
        result.winner = 0;
    } else if (winner == 1) {
        stacks[1] += pot;
        result.winner = 1;
    } else {
        // Split pot (give remainder to player 0)
        stacks[0] += pot / 2 + (pot % 2);
        stacks[1] += pot / 2;
        result.winner = -1;
    }
    
    result.pot_size = pot;
    
    return result;
}

MatchResult Simulator::simulate_match(Bot* bot0, Bot* bot1, int num_hands) {
    MatchResult result = {};
    result.hands_played = 0;  // Will count actual hands played
    result.p0_wins_by_rank.assign(9, 0);
    result.p1_wins_by_rank.assign(9, 0);
    
    std::array<int, 2> stacks = {config_.initial_stack, config_.initial_stack};
    
    for (int i = 0; i < num_hands; ++i) {
        int button = i % 2;
        
        // Check if either player is out
        if (stacks[0] <= 0 || stacks[1] <= 0) {
            break;
        }
        
        result.hands_played++;  // Increment for each hand actually played
        
        // Alternate positions based on button for fairness
        Bot* pos0_bot = (button == 0) ? bot0 : bot1;
        Bot* pos1_bot = (button == 0) ? bot1 : bot0;
        std::array<int, 2> pos_stacks = (button == 0) ? stacks : std::array<int,2>{stacks[1], stacks[0]};
        
        HandResult hand_result = simulate_hand(pos0_bot, pos1_bot, pos_stacks, button);
        
        // Map winner back to original bot0/bot1
        int actual_winner = hand_result.winner;
        if (button == 1 && actual_winner >= 0) {
            actual_winner = 1 - actual_winner;  // Swap winner mapping
        }
        
        // Unswap stacks
        if (button == 1) {
            stacks[0] = pos_stacks[1];
            stacks[1] = pos_stacks[0];
        } else {
            stacks = pos_stacks;
        }
        
        // Update statistics with corrected winner
        // Map showdown ranks based on button position
        int p0_rank = (button == 0) ? hand_result.p0_showdown_rank : hand_result.p1_showdown_rank;
        int p1_rank = (button == 0) ? hand_result.p1_showdown_rank : hand_result.p0_showdown_rank;
        
        if (actual_winner == 0) {
            result.p0_wins++;
            if (p0_rank >= 0 && p0_rank < 9) {
                result.p0_wins_by_rank[p0_rank]++;
            }
        } else if (actual_winner == 1) {
            result.p1_wins++;
            if (p1_rank >= 0 && p1_rank < 9) {
                result.p1_wins_by_rank[p1_rank]++;
            }
        } else {
            result.ties++;
        }
        
        // Aggregate action counts (fold/call/raise) from per-hand logs
        // Need to remap actions when button == 1 (positions were swapped)
        const std::vector<Action>& bot0_actions = (button == 0) ? hand_result.p0_actions : hand_result.p1_actions;
        const std::vector<Action>& bot1_actions = (button == 0) ? hand_result.p1_actions : hand_result.p0_actions;
        
        for (auto a : bot0_actions) {
            if (a == Action::FOLD) result.p0_folds++;
            else if (a == Action::CALL) result.p0_calls++;
            else if (a == Action::RAISE || a == Action::BET) result.p0_raises++;
        }
        for (auto a : bot1_actions) {
            if (a == Action::FOLD) result.p1_folds++;
            else if (a == Action::CALL) result.p1_calls++;
            else if (a == Action::RAISE || a == Action::BET) result.p1_raises++;
        }
    }
    
    result.p0_final_stack = stacks[0];
    result.p1_final_stack = stacks[1];
    
    // Determine match winner by final stack size
    if (stacks[0] > stacks[1]) {
        result.match_winner = 0;  // Player 0 wins the match
    } else if (stacks[1] > stacks[0]) {
        result.match_winner = 1;  // Player 1 wins the match
    } else {
        result.match_winner = -1; // Tie
    }
    
    int total_decided = result.p0_wins + result.p1_wins;
    if (total_decided > 0) {
        result.p0_win_rate = static_cast<double>(result.p0_wins) / total_decided;
        result.p1_win_rate = static_cast<double>(result.p1_wins) / total_decided;
    }
    
    return result;
}

std::vector<MatchResult> Simulator::simulate_batch(
    Bot* bot0,
    Bot* bot1,
    int num_matches,
    int hands_per_match
) {
    std::vector<MatchResult> results;
    results.reserve(num_matches);
    
    for (int i = 0; i < num_matches; ++i) {
        results.push_back(simulate_match(bot0, bot1, hands_per_match));
    }
    
    return results;
}

} // namespace poker

