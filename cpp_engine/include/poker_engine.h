#pragma once

#include <cstdint>
#include <vector>
#include <string>

namespace poker {

/**
 * Card representation (0-51 encoding)
 * Cards are encoded as: (rank - 2) * 4 + suit
 * Ranks: 2-14 (where 14 = Ace)
 * Suits: 0=Clubs, 1=Diamonds, 2=Hearts, 3=Spades
 */
using Card = uint8_t;

/**
 * Action types for poker decisions
 */
enum class Action : uint8_t {
    FOLD = 0,
    CHECK = 1,
    CALL = 2,
    BET = 3,
    RAISE = 4
};

/**
 * Hand strength categories
 */
enum class HandRank : uint8_t {
    HIGH_CARD = 0,
    PAIR = 1,
    TWO_PAIR = 2,
    THREE_OF_A_KIND = 3,
    STRAIGHT = 4,
    FLUSH = 5,
    FULL_HOUSE = 6,
    FOUR_OF_A_KIND = 7,
    STRAIGHT_FLUSH = 8
};

/**
 * Result of a single poker hand
 */
struct HandResult {
    int winner;           // 0, 1, or -1 for tie
    int pot_size;
    int hands_played;
    std::vector<Action> p0_actions;
    std::vector<Action> p1_actions;
    int p0_showdown_rank = -1; // -1 if no showdown
    int p1_showdown_rank = -1; // -1 if no showdown
};

/**
 * Result of a match (multiple hands)
 */
struct MatchResult {
    int hands_played;
    int p0_wins;
    int p1_wins;
    int ties;
    int p0_final_stack;
    int p1_final_stack;
    double p0_win_rate;
    double p1_win_rate;
    int match_winner;  // 0 = p0 wins, 1 = p1 wins, -1 = tie
    
    // Action statistics
    int p0_folds;
    int p0_calls;
    int p0_raises;
    int p1_folds;
    int p1_calls;
    int p1_raises;

    // Showdown win breakdown by HandRank (size 9: HIGH_CARD..STRAIGHT_FLUSH)
    std::vector<int> p0_wins_by_rank;
    std::vector<int> p1_wins_by_rank;
};

/**
 * Configuration for simulation
 */
struct SimConfig {
    int initial_stack = 1000;
    int small_blind = 5;
    int big_blind = 10;
    uint64_t seed = 12345;
};

// Utility functions
std::string card_to_string(Card card);
Card string_to_card(const std::string& str);
int get_rank(Card card);
int get_suit(Card card);

} // namespace poker

