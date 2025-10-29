#pragma once

#include "poker_engine.h"
#include <array>

namespace poker {

/**
 * Fast poker hand evaluation using lookup tables.
 * 
 * Evaluates 7-card poker hands (2 hole + 5 community) and returns
 * a score that can be compared to determine winner.
 */
class HandEvaluator {
public:
    /**
     * Evaluate a 7-card hand and return numeric strength score.
     * Higher scores are better. Scores can be compared directly.
     * 
     * @param cards Array of 7 cards (2 hole + 5 community)
     * @return Numeric hand strength (higher = better)
     */
    static uint32_t evaluate_7cards(const std::array<Card, 7>& cards);
    
    /**
     * Evaluate best 5-card hand from any number of cards.
     * 
     * @param cards Vector of cards (minimum 5, maximum 7 typically)
     * @return Numeric hand strength
     */
    static uint32_t evaluate(const std::vector<Card>& cards);
    
    /**
     * Get hand rank category (HIGH_CARD, PAIR, etc.)
     * 
     * @param score Evaluation score from evaluate()
     * @return Hand rank category
     */
    static HandRank get_hand_rank(uint32_t score);
    
    /**
     * Get human-readable hand description.
     * 
     * @param score Evaluation score
     * @return String like "Full House, Kings over Tens"
     */
    static std::string describe_hand(uint32_t score);
    
private:
    // Simplified evaluation for initial implementation
    static uint32_t evaluate_simple(const std::vector<Card>& cards);
    
    // Helper functions
    static bool is_flush(const std::vector<Card>& cards);
    static bool is_straight(std::vector<int> ranks);
    static std::vector<int> get_rank_counts(const std::vector<Card>& cards);
};

/**
 * Monte Carlo equity calculator.
 * 
 * Estimates win probability by randomly dealing out unknown cards
 * and evaluating outcomes.
 */
class EquityCalculator {
public:
    /**
     * Calculate equity for hole cards vs opponent range.
     * 
     * @param hero_cards Hero's 2 hole cards
     * @param board Community cards (0-5 cards)
     * @param num_opponents Number of opponents (typically 1 for HU)
     * @param iterations Number of Monte Carlo samples
     * @param seed Random seed
     * @return Win probability (0.0 - 1.0)
     */
    static double calculate_equity(
        const std::array<Card, 2>& hero_cards,
        const std::vector<Card>& board,
        int num_opponents,
        int iterations,
        uint64_t seed
    );
    
    /**
     * Fast batch equity calculation for multiple scenarios.
     */
    static std::vector<double> calculate_equity_batch(
        const std::vector<std::array<Card, 2>>& hero_hands,
        const std::vector<Card>& board,
        int num_opponents,
        int iterations,
        uint64_t seed
    );
};

} // namespace poker

