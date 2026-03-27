"""
test_project.py — pytest test suite for SciQuiz Pro
CS50P Final Project

Tests for: load_questions, calculate_score, filter_questions,
           save_score, load_history, format_leaderboard
"""

import json
import csv
import os
import pytest
import tempfile

from project import (
    load_questions,
    calculate_score,
    filter_questions,
    save_score,
    load_history,
    format_leaderboard,
)


# ═══════════════════════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════════════════════

SAMPLE_QUESTIONS = [
    {
        "category": "Química",
        "difficulty": "easy",
        "question": "¿Símbolo del oro?",
        "options": ["Au", "Ag", "Fe", "Cu"],
        "answer": "Au",
        "explanation": "Aurum en latín.",
    },
    {
        "category": "Física",
        "difficulty": "medium",
        "question": "¿Velocidad de la luz?",
        "options": ["3×10⁸ m/s", "3×10⁶ m/s", "3×10⁴ m/s", "3×10¹⁰ m/s"],
        "answer": "3×10⁸ m/s",
        "explanation": "c ≈ 3×10⁸ m/s.",
    },
    {
        "category": "Química",
        "difficulty": "hard",
        "question": "Variable fundamental del DFT?",
        "options": ["Función de onda", "Densidad electrónica", "Energía", "Potencial"],
        "answer": "Densidad electrónica",
        "explanation": "Teoremas de Hohenberg-Kohn.",
    },
    {
        "category": "Astronomía",
        "difficulty": "easy",
        "question": "¿Planetas en el Sistema Solar?",
        "options": ["7", "8", "9", "10"],
        "answer": "8",
        "explanation": "Plutón es planeta enano desde 2006.",
    },
]


@pytest.fixture
def sample_json(tmp_path):
    """Write SAMPLE_QUESTIONS to a temp JSON file and return its path."""
    p = tmp_path / "questions.json"
    p.write_text(json.dumps(SAMPLE_QUESTIONS), encoding="utf-8")
    return str(p)


@pytest.fixture
def history_csv(tmp_path):
    """Return a path to a temp CSV file (does not create the file)."""
    return str(tmp_path / "history.csv")


# ═══════════════════════════════════════════════════════════════════════════════
# TESTS: load_questions
# ═══════════════════════════════════════════════════════════════════════════════

def test_load_questions_returns_list(sample_json):
    questions = load_questions(sample_json)
    assert isinstance(questions, list)


def test_load_questions_correct_count(sample_json):
    questions = load_questions(sample_json)
    assert len(questions) == len(SAMPLE_QUESTIONS)


def test_load_questions_has_required_keys(sample_json):
    questions = load_questions(sample_json)
    required = {"category", "difficulty", "question", "options", "answer", "explanation"}
    for q in questions:
        assert required.issubset(q.keys()), f"Missing keys in: {q}"


def test_load_questions_file_not_found():
    with pytest.raises(FileNotFoundError):
        load_questions("/nonexistent/path/questions.json")


def test_load_questions_invalid_json(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("NOT VALID JSON", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid JSON"):
        load_questions(str(bad))


def test_load_questions_empty_array(tmp_path):
    empty = tmp_path / "empty.json"
    empty.write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError, match="non-empty"):
        load_questions(str(empty))


# ═══════════════════════════════════════════════════════════════════════════════
# TESTS: calculate_score
# ═══════════════════════════════════════════════════════════════════════════════

def test_calculate_score_no_streak():
    """With no streak (streak=0), multiplier is 1×."""
    assert calculate_score(1, 0) == 1
    assert calculate_score(2, 0) == 2
    assert calculate_score(3, 0) == 3


def test_calculate_score_streak_bonus():
    """Every 3 consecutive correct answers adds 0.5× multiplier."""
    # streak=3 → multiplier = 1 + 0.5×1 = 1.5
    assert calculate_score(2, 3) == int(2 * 1.5)   # 3
    # streak=6 → multiplier = 1 + 0.5×2 = 2.0
    assert calculate_score(2, 6) == int(2 * 2.0)   # 4


def test_calculate_score_cap():
    """Multiplier caps at 4×, regardless of streak length."""
    # streak=18 → uncapped = 1+0.5×6 = 4.0 (exactly at cap)
    assert calculate_score(3, 18) == int(3 * 4.0)
    # streak=30 → would be 1+0.5×10 = 6.0 but capped at 4
    assert calculate_score(3, 30) == int(3 * 4.0)


def test_calculate_score_time_bonus():
    """time_bonus is added directly to the result."""
    assert calculate_score(1, 0, time_bonus=5) == 6


def test_calculate_score_negative_base_raises():
    with pytest.raises(ValueError):
        calculate_score(-1, 0)


def test_calculate_score_negative_streak_raises():
    with pytest.raises(ValueError):
        calculate_score(1, -1)


def test_calculate_score_returns_int():
    result = calculate_score(3, 3)
    assert isinstance(result, int)


# ═══════════════════════════════════════════════════════════════════════════════
# TESTS: filter_questions
# ═══════════════════════════════════════════════════════════════════════════════

def test_filter_questions_no_filter():
    result = filter_questions(SAMPLE_QUESTIONS)
    assert len(result) == len(SAMPLE_QUESTIONS)


def test_filter_questions_by_category():
    result = filter_questions(SAMPLE_QUESTIONS, categories=["Química"])
    assert all(q["category"] == "Química" for q in result)
    assert len(result) == 2


def test_filter_questions_by_difficulty():
    result = filter_questions(SAMPLE_QUESTIONS, difficulty="easy")
    assert all(q["difficulty"] == "easy" for q in result)
    assert len(result) == 2


def test_filter_questions_category_and_difficulty():
    result = filter_questions(SAMPLE_QUESTIONS, categories=["Química"], difficulty="hard")
    assert len(result) == 1
    assert result[0]["answer"] == "Densidad electrónica"


def test_filter_questions_no_match_returns_empty():
    result = filter_questions(SAMPLE_QUESTIONS, categories=["Biología"], difficulty="hard")
    assert result == []


def test_filter_questions_invalid_difficulty_raises():
    with pytest.raises(ValueError, match="difficulty"):
        filter_questions(SAMPLE_QUESTIONS, difficulty="ultrahard")


def test_filter_questions_multiple_categories():
    result = filter_questions(SAMPLE_QUESTIONS, categories=["Química", "Astronomía"])
    categories_found = {q["category"] for q in result}
    assert categories_found == {"Química", "Astronomía"}


# ═══════════════════════════════════════════════════════════════════════════════
# TESTS: save_score & load_history
# ═══════════════════════════════════════════════════════════════════════════════

def test_save_score_creates_file(history_csv):
    save_score("Alice", 15, 5, "Química", "easy", filepath=history_csv)
    assert os.path.exists(history_csv)


def test_save_score_writes_correct_data(history_csv):
    save_score("Bob", 30, 10, "Física", "medium", filepath=history_csv)
    history = load_history(filepath=history_csv)
    assert len(history) == 1
    assert history[0]["player"] == "Bob"
    assert history[0]["score"] == "30"
    assert history[0]["questions"] == "10"
    assert history[0]["category"] == "Física"
    assert history[0]["difficulty"] == "medium"


def test_save_score_appends_multiple(history_csv):
    save_score("Alice", 10, 5, "Química", "easy",   filepath=history_csv)
    save_score("Alice", 20, 5, "Física",  "medium", filepath=history_csv)
    save_score("Bob",   15, 5, "Mixta",   "Mixta",  filepath=history_csv)
    history = load_history(filepath=history_csv)
    assert len(history) == 3


def test_load_history_empty_when_no_file(tmp_path):
    result = load_history(filepath=str(tmp_path / "nonexistent.csv"))
    assert result == []


def test_load_history_returns_list_of_dicts(history_csv):
    save_score("Carol", 5, 5, "Mixta", "Mixta", filepath=history_csv)
    history = load_history(filepath=history_csv)
    assert isinstance(history, list)
    assert isinstance(history[0], dict)


# ═══════════════════════════════════════════════════════════════════════════════
# TESTS: format_leaderboard
# ═══════════════════════════════════════════════════════════════════════════════

def test_format_leaderboard_empty():
    result = format_leaderboard([])
    assert "No hay partidas" in result


def test_format_leaderboard_contains_player_name():
    history = [
        {"player": "Yoh", "score": "42", "timestamp": "2025-01-01 10:00"}
    ]
    result = format_leaderboard(history)
    assert "Yoh" in result


def test_format_leaderboard_sorted_descending():
    history = [
        {"player": "PlayerLow",  "score": "10", "timestamp": "2025-01-01 10:00"},
        {"player": "PlayerHigh", "score": "50", "timestamp": "2025-01-02 10:00"},
        {"player": "PlayerMid",  "score": "30", "timestamp": "2025-01-03 10:00"},
    ]
    result = format_leaderboard(history)
    pos_high = result.index("PlayerHigh")
    pos_mid  = result.index("PlayerMid")
    pos_low  = result.index("PlayerLow")
    assert pos_high < pos_mid < pos_low   # 50 → 30 → 10


def test_format_leaderboard_respects_top_n():
    history = [
        {"player": f"P{i}", "score": str(i * 10), "timestamp": "2025-01-01 10:00"}
        for i in range(10)
    ]
    result = format_leaderboard(history, top_n=3)
    # Only top 3 players should appear; P0 (score 0) should not
    assert "P0" not in result


def test_format_leaderboard_returns_string():
    history = [{"player": "X", "score": "5", "timestamp": "2025-01-01 10:00"}]
    assert isinstance(format_leaderboard(history), str)
