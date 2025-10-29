#pragma once

#include "poker_engine.h"
#include "hand_evaluator.h"
#include <random>
#include <memory>

namespace poker {

/**
 * Abstract bot interface for C++ simulation.
 * 
 * Bots can be implemented in C++ for maximum performance,
 * or called from Python via pybind11.
 */
class Bot {
public:
    virtual ~Bot() = default;
    
    /**
     * Make a decision given current game state.
     * 
     * @param hole_cards Bot's 2 hole cards
     * @param board Community cards (0-5 cards)
     * @param pot Current pot size
     * @param to_call Amount needed to call
     * @param stack Remaining stack
     * @param can_check Whether checking is allowed
     * @return Chosen action
     */
    virtual Action get_action(
        const std::array<Card, 2>& hole_cards,
        const std::vector<Card>& board,
        int pot,
        int to_call,
        int stack,
        bool can_check
    ) = 0;
    
    /**
     * Get bet/raise sizing when action is BET or RAISE.
     */
    virtual int get_bet_size(int pot, int stack) = 0;
};

// C++ bot implementations removed - use Python bots via pybind11 trampoline

/**
 * High-performance poker simulator.
 * 
 * Simulates complete poker matches between two bots at maximum speed.
 */
class Simulator {
public:
    explicit Simulator(const SimConfig& config);
    
    /**
     * Simulate a single hand between two bots.
     * 
     * @param bot0 First bot
     * @param bot1 Second bot
     * @param stacks Current stack sizes [bot0, bot1]
     * @param button Current button position (0 or 1)
     * @return Hand result
     */
    HandResult simulate_hand(
        Bot* bot0,
        Bot* bot1,
        std::array<int, 2>& stacks,
        int button
    );
    
    /**
     * Simulate complete match of multiple hands.
     * 
     * @param bot0 First bot
     * @param bot1 Second bot
     * @param num_hands Number of hands to play
     * @return Match statistics
     */
    MatchResult simulate_match(
        Bot* bot0,
        Bot* bot1,
        int num_hands
    );
    
    /**
     * Batch simulation for statistical analysis.
     * Run multiple independent matches in sequence.
     * 
     * @param bot0 First bot
     * @param bot1 Second bot
     * @param num_matches Number of matches
     * @param hands_per_match Hands per match
     * @return Vector of match results
     */
    std::vector<MatchResult> simulate_batch(
        Bot* bot0,
        Bot* bot1,
        int num_matches,
        int hands_per_match
    );
    
private:
    SimConfig config_;
    std::mt19937_64 rng_;
    
    // Internal simulation helpers
    void deal_cards(std::array<Card, 2>& p0_cards, std::array<Card, 2>& p1_cards);
    std::vector<Card> deal_board();
    int resolve_showdown(
        const std::array<Card, 2>& p0_cards,
        const std::array<Card, 2>& p1_cards,
        const std::vector<Card>& board
    );
    
    int simulate_betting_round(
        Bot* bot0,
        Bot* bot1,
        const std::array<Card, 2>& p0_cards,
        const std::array<Card, 2>& p1_cards,
        const std::vector<Card>& board,
        int& pot,
        std::array<int, 2>& stacks,
        std::array<int, 2>& current_bets,
        HandResult& hand_log
    );
};

} // namespace poker

