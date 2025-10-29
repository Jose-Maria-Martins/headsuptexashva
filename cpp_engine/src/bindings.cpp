#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/numpy.h>

#include "poker_engine.h"
#include "hand_evaluator.h"
#include "simulator.h"

namespace py = pybind11;

PYBIND11_MODULE(poker_engine, m) {
    m.doc() = "High-performance C++ poker simulation engine";
    m.attr("__version__") = "0.1.0";
    
    // Enums
    py::enum_<poker::Action>(m, "Action")
        .value("FOLD", poker::Action::FOLD)
        .value("CHECK", poker::Action::CHECK)
        .value("CALL", poker::Action::CALL)
        .value("BET", poker::Action::BET)
        .value("RAISE", poker::Action::RAISE)
        .export_values();
    
    py::enum_<poker::HandRank>(m, "HandRank")
        .value("HIGH_CARD", poker::HandRank::HIGH_CARD)
        .value("PAIR", poker::HandRank::PAIR)
        .value("TWO_PAIR", poker::HandRank::TWO_PAIR)
        .value("THREE_OF_A_KIND", poker::HandRank::THREE_OF_A_KIND)
        .value("STRAIGHT", poker::HandRank::STRAIGHT)
        .value("FLUSH", poker::HandRank::FLUSH)
        .value("FULL_HOUSE", poker::HandRank::FULL_HOUSE)
        .value("FOUR_OF_A_KIND", poker::HandRank::FOUR_OF_A_KIND)
        .value("STRAIGHT_FLUSH", poker::HandRank::STRAIGHT_FLUSH)
        .export_values();
    
    // Structs
    py::class_<poker::HandResult>(m, "HandResult")
        .def(py::init<>())
        .def_readwrite("winner", &poker::HandResult::winner)
        .def_readwrite("pot_size", &poker::HandResult::pot_size)
        .def_readwrite("hands_played", &poker::HandResult::hands_played)
        .def_readwrite("p0_actions", &poker::HandResult::p0_actions)
        .def_readwrite("p1_actions", &poker::HandResult::p1_actions)
        .def_readwrite("p0_showdown_rank", &poker::HandResult::p0_showdown_rank)
        .def_readwrite("p1_showdown_rank", &poker::HandResult::p1_showdown_rank);
    
    py::class_<poker::MatchResult>(m, "MatchResult")
        .def(py::init<>())
        .def_readwrite("hands_played", &poker::MatchResult::hands_played)
        .def_readwrite("p0_wins", &poker::MatchResult::p0_wins)
        .def_readwrite("p1_wins", &poker::MatchResult::p1_wins)
        .def_readwrite("ties", &poker::MatchResult::ties)
        .def_readwrite("p0_final_stack", &poker::MatchResult::p0_final_stack)
        .def_readwrite("p1_final_stack", &poker::MatchResult::p1_final_stack)
        .def_readwrite("p0_win_rate", &poker::MatchResult::p0_win_rate)
        .def_readwrite("p1_win_rate", &poker::MatchResult::p1_win_rate)
        .def_readwrite("match_winner", &poker::MatchResult::match_winner)
        .def_readwrite("p0_folds", &poker::MatchResult::p0_folds)
        .def_readwrite("p0_calls", &poker::MatchResult::p0_calls)
        .def_readwrite("p0_raises", &poker::MatchResult::p0_raises)
        .def_readwrite("p1_folds", &poker::MatchResult::p1_folds)
        .def_readwrite("p1_calls", &poker::MatchResult::p1_calls)
        .def_readwrite("p1_raises", &poker::MatchResult::p1_raises)
        .def_readwrite("p0_wins_by_rank", &poker::MatchResult::p0_wins_by_rank)
        .def_readwrite("p1_wins_by_rank", &poker::MatchResult::p1_wins_by_rank);
    
    py::class_<poker::SimConfig>(m, "SimConfig")
        .def(py::init<>())
        .def_readwrite("initial_stack", &poker::SimConfig::initial_stack)
        .def_readwrite("small_blind", &poker::SimConfig::small_blind)
        .def_readwrite("big_blind", &poker::SimConfig::big_blind)
        .def_readwrite("seed", &poker::SimConfig::seed);
    
    // Utility functions
    m.def("card_to_string", &poker::card_to_string, 
          "Convert card ID to string representation");
    m.def("string_to_card", &poker::string_to_card,
          "Parse card from string (e.g., 'As', 'Kh')");
    m.def("get_rank", &poker::get_rank,
          "Get rank from card ID (0-12)");
    m.def("get_suit", &poker::get_suit,
          "Get suit from card ID (0-3)");
    
    // HandEvaluator
    py::class_<poker::HandEvaluator>(m, "HandEvaluator")
        .def_static("evaluate", 
                    py::overload_cast<const std::vector<poker::Card>&>(&poker::HandEvaluator::evaluate),
                    "Evaluate poker hand strength")
        .def_static("get_hand_rank", &poker::HandEvaluator::get_hand_rank,
                    "Get hand rank category from evaluation score")
        .def_static("describe_hand", &poker::HandEvaluator::describe_hand,
                    "Get human-readable hand description");
    
    // EquityCalculator
    py::class_<poker::EquityCalculator>(m, "EquityCalculator")
        .def_static("calculate_equity", &poker::EquityCalculator::calculate_equity,
                    py::arg("hero_cards"),
                    py::arg("board"),
                    py::arg("num_opponents") = 1,
                    py::arg("iterations") = 10000,
                    py::arg("seed") = 12345,
                    "Calculate hand equity via Monte Carlo simulation")
        .def_static("calculate_equity_batch", &poker::EquityCalculator::calculate_equity_batch,
                    py::arg("hero_hands"),
                    py::arg("board"),
                    py::arg("num_opponents") = 1,
                    py::arg("iterations") = 10000,
                    py::arg("seed") = 12345,
                    "Calculate equity for multiple hands");
    
    // Python-subclassable Bot via trampoline
    struct PyBot : poker::Bot {
        using poker::Bot::Bot;
        poker::Action get_action(
            const std::array<poker::Card, 2>& hole_cards,
            const std::vector<poker::Card>& board,
            int pot,
            int to_call,
            int stack,
            bool can_check
        ) override {
            PYBIND11_OVERRIDE_PURE(
                poker::Action,
                poker::Bot,
                get_action,
                hole_cards,
                board,
                pot,
                to_call,
                stack,
                can_check
            );
        }
        int get_bet_size(int pot, int stack) override {
            PYBIND11_OVERRIDE_PURE(
                int,
                poker::Bot,
                get_bet_size,
                pot,
                stack
            );
        }
    };

    py::class_<poker::Bot, PyBot>(m, "Bot")
        .def(py::init<>())
        .def("get_action", &poker::Bot::get_action)
        .def("get_bet_size", &poker::Bot::get_bet_size);
    
    // C++ bot bindings removed - bots are implemented in Python
    
    // Simulator
    py::class_<poker::Simulator>(m, "Simulator")
        .def(py::init<const poker::SimConfig&>())
        .def("simulate_match", &poker::Simulator::simulate_match,
             py::arg("bot0"),
             py::arg("bot1"),
             py::arg("num_hands"),
             "Simulate a match of multiple hands")
        .def("simulate_batch", &poker::Simulator::simulate_batch,
             py::arg("bot0"),
             py::arg("bot1"),
             py::arg("num_matches"),
             py::arg("hands_per_match"),
             "Simulate multiple matches for statistical analysis");
    
    // Convenience function removed - use Python bots instead
    
    m.def("evaluate_hand_string",
        [](const std::vector<std::string>& card_strings) {
            std::vector<poker::Card> cards;
            for (const auto& s : card_strings) {
                cards.push_back(poker::string_to_card(s));
            }
            uint32_t score = poker::HandEvaluator::evaluate(cards);
            return py::make_tuple(
                score,
                poker::HandEvaluator::describe_hand(score)
            );
        },
        py::arg("cards"),
        "Evaluate hand from string representation");
}

