#include "hand_evaluator.h"
#include <algorithm>
#include <map>
#include <random>

namespace poker {

uint32_t HandEvaluator::evaluate_7cards(const std::array<Card, 7>& cards) {
    std::vector<Card> card_vec(cards.begin(), cards.end());
    return evaluate(card_vec);
}

uint32_t HandEvaluator::evaluate(const std::vector<Card>& cards) {
    if (cards.size() < 5) {
        return 0;
    }
    return evaluate_simple(cards);
}

uint32_t HandEvaluator::evaluate_simple(const std::vector<Card>& cards) {
    // Extract ranks and suits
    std::vector<int> ranks;
    for (Card card : cards) {
        ranks.push_back(get_rank(card));
    }
    std::sort(ranks.begin(), ranks.end(), std::greater<int>());
    
    // Count rank frequencies
    std::map<int, int> rank_counts;
    for (int rank : ranks) {
        rank_counts[rank]++;
    }
    
    // Get frequency groups
    std::vector<std::pair<int, int>> groups; // (count, rank)
    for (const auto& [rank, count] : rank_counts) {
        groups.emplace_back(count, rank);
    }
    std::sort(groups.begin(), groups.end(), [](const auto& a, const auto& b) {
        if (a.first != b.first) return a.first > b.first;
        return a.second > b.second;
    });
    
    bool is_flush_hand = is_flush(cards);
    bool is_straight_hand = is_straight(ranks);
    
    uint32_t score = 0;
    
    // Straight Flush
    if (is_flush_hand && is_straight_hand) {
        score = 8000000 + ranks[0];
    }
    // Four of a Kind
    else if (groups[0].first == 4) {
        score = 7000000 + groups[0].second * 1000 + groups[1].second;
    }
    // Full House
    else if (groups[0].first == 3 && groups[1].first >= 2) {
        score = 6000000 + groups[0].second * 1000 + groups[1].second;
    }
    // Flush
    else if (is_flush_hand) {
        score = 5000000;
        for (size_t i = 0; i < std::min(size_t(5), ranks.size()); ++i) {
            score += ranks[i] * (1 << (4 - i));
        }
    }
    // Straight
    else if (is_straight_hand) {
        score = 4000000 + ranks[0];
    }
    // Three of a Kind
    else if (groups[0].first == 3) {
        score = 3000000 + groups[0].second * 10000;
        if (groups.size() > 1) score += groups[1].second * 100;
        if (groups.size() > 2) score += groups[2].second;
    }
    // Two Pair
    else if (groups[0].first == 2 && groups[1].first == 2) {
        score = 2000000 + groups[0].second * 10000 + groups[1].second * 100;
        if (groups.size() > 2) score += groups[2].second;
    }
    // One Pair
    else if (groups[0].first == 2) {
        score = 1000000 + groups[0].second * 100000;
        for (size_t i = 1; i < std::min(size_t(4), groups.size()); ++i) {
            score += groups[i].second * (1 << (3 - i));
        }
    }
    // High Card
    else {
        score = 0;
        for (size_t i = 0; i < std::min(size_t(5), ranks.size()); ++i) {
            score += ranks[i] * (1 << (4 - i));
        }
    }
    
    return score;
}

bool HandEvaluator::is_flush(const std::vector<Card>& cards) {
    if (cards.size() < 5) return false;
    
    std::map<int, int> suit_counts;
    for (Card card : cards) {
        suit_counts[get_suit(card)]++;
        if (suit_counts[get_suit(card)] >= 5) {
            return true;
        }
    }
    return false;
}

bool HandEvaluator::is_straight(std::vector<int> ranks) {
    // Remove duplicates and sort
    std::sort(ranks.begin(), ranks.end(), std::greater<int>());
    ranks.erase(std::unique(ranks.begin(), ranks.end()), ranks.end());
    
    if (ranks.size() < 5) return false;
    
    // Check for regular straight
    for (size_t i = 0; i <= ranks.size() - 5; ++i) {
        bool is_consecutive = true;
        for (size_t j = 0; j < 4; ++j) {
            if (ranks[i + j] - ranks[i + j + 1] != 1) {
                is_consecutive = false;
                break;
            }
        }
        if (is_consecutive) return true;
    }
    
    // Check for wheel (A-2-3-4-5)
    if (ranks[0] == 12 && ranks[ranks.size() - 4] == 3 && 
        ranks[ranks.size() - 3] == 2 && ranks[ranks.size() - 2] == 1 && 
        ranks[ranks.size() - 1] == 0) {
        return true;
    }
    
    return false;
}

HandRank HandEvaluator::get_hand_rank(uint32_t score) {
    if (score >= 8000000) return HandRank::STRAIGHT_FLUSH;
    if (score >= 7000000) return HandRank::FOUR_OF_A_KIND;
    if (score >= 6000000) return HandRank::FULL_HOUSE;
    if (score >= 5000000) return HandRank::FLUSH;
    if (score >= 4000000) return HandRank::STRAIGHT;
    if (score >= 3000000) return HandRank::THREE_OF_A_KIND;
    if (score >= 2000000) return HandRank::TWO_PAIR;
    if (score >= 1000000) return HandRank::PAIR;
    return HandRank::HIGH_CARD;
}

std::string HandEvaluator::describe_hand(uint32_t score) {
    HandRank rank = get_hand_rank(score);
    
    switch (rank) {
        case HandRank::STRAIGHT_FLUSH: return "Straight Flush";
        case HandRank::FOUR_OF_A_KIND: return "Four of a Kind";
        case HandRank::FULL_HOUSE: return "Full House";
        case HandRank::FLUSH: return "Flush";
        case HandRank::STRAIGHT: return "Straight";
        case HandRank::THREE_OF_A_KIND: return "Three of a Kind";
        case HandRank::TWO_PAIR: return "Two Pair";
        case HandRank::PAIR: return "Pair";
        case HandRank::HIGH_CARD: return "High Card";
        default: return "Unknown";
    }
}

// EquityCalculator implementation
double EquityCalculator::calculate_equity(
    const std::array<Card, 2>& hero_cards,
    const std::vector<Card>& board,
    int num_opponents,
    int iterations,
    uint64_t seed
) {
    std::mt19937_64 rng(seed);
    
    // Build deck of remaining cards
    std::vector<Card> deck;
    std::vector<bool> used(52, false);
    
    for (Card c : hero_cards) used[c] = true;
    for (Card c : board) used[c] = true;
    
    for (Card c = 0; c < 52; ++c) {
        if (!used[c]) deck.push_back(c);
    }
    
    int wins = 0;
    int ties = 0;
    
    for (int iter = 0; iter < iterations; ++iter) {
        // Shuffle remaining deck
        std::shuffle(deck.begin(), deck.end(), rng);
        
        // Deal opponent cards
        std::array<Card, 2> opp_cards = {deck[0], deck[1]};
        
        // Complete board if needed
        std::vector<Card> full_board = board;
        int cards_dealt = 2;
        while (full_board.size() < 5) {
            full_board.push_back(deck[cards_dealt++]);
        }
        
        // Evaluate hands
        std::vector<Card> hero_hand = {hero_cards[0], hero_cards[1]};
        hero_hand.insert(hero_hand.end(), full_board.begin(), full_board.end());
        
        std::vector<Card> opp_hand = {opp_cards[0], opp_cards[1]};
        opp_hand.insert(opp_hand.end(), full_board.begin(), full_board.end());
        
        uint32_t hero_score = HandEvaluator::evaluate(hero_hand);
        uint32_t opp_score = HandEvaluator::evaluate(opp_hand);
        
        if (hero_score > opp_score) {
            wins++;
        } else if (hero_score == opp_score) {
            ties++;
        }
    }
    
    return (wins + ties * 0.5) / iterations;
}

std::vector<double> EquityCalculator::calculate_equity_batch(
    const std::vector<std::array<Card, 2>>& hero_hands,
    const std::vector<Card>& board,
    int num_opponents,
    int iterations,
    uint64_t seed
) {
    std::vector<double> results;
    results.reserve(hero_hands.size());
    
    for (const auto& hand : hero_hands) {
        results.push_back(calculate_equity(hand, board, num_opponents, iterations, seed++));
    }
    
    return results;
}

} // namespace poker

