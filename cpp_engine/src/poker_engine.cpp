#include "poker_engine.h"
#include <cctype>
#include <sstream>

namespace poker {

std::string card_to_string(Card card) {
    const char ranks[] = "23456789TJQKA";
    const char suits[] = "cdhs";
    
    int rank = get_rank(card);
    int suit = get_suit(card);
    
    std::string result;
    result += ranks[rank];
    result += suits[suit];
    return result;
}

Card string_to_card(const std::string& str) {
    if (str.length() != 2) {
        throw std::invalid_argument("Card string must be exactly 2 characters");
    }
    
    // Parse rank
    char rank_char = static_cast<char>(std::toupper(static_cast<unsigned char>(str[0])));
    int rank = -1;
    
    if (rank_char >= '2' && rank_char <= '9') {
        rank = rank_char - '2';
    } else if (rank_char == 'T') {
        rank = 8;
    } else if (rank_char == 'J') {
        rank = 9;
    } else if (rank_char == 'Q') {
        rank = 10;
    } else if (rank_char == 'K') {
        rank = 11;
    } else if (rank_char == 'A') {
        rank = 12;
    } else {
        throw std::invalid_argument("Invalid rank character");
    }
    
    // Parse suit
    char suit_char = static_cast<char>(std::tolower(static_cast<unsigned char>(str[1])));
    int suit = -1;
    
    if (suit_char == 'c') {
        suit = 0;
    } else if (suit_char == 'd') {
        suit = 1;
    } else if (suit_char == 'h') {
        suit = 2;
    } else if (suit_char == 's') {
        suit = 3;
    } else {
        throw std::invalid_argument("Invalid suit character");
    }
    
    return static_cast<Card>(rank * 4 + suit);
}

int get_rank(Card card) {
    return card / 4;
}

int get_suit(Card card) {
    return card % 4;
}

} // namespace poker

