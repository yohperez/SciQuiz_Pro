"""
SciQuiz Pro — CLI Scientific Trivia Game
CS50P Final Project
Author: [Your Name]

A command-line trivia game with 6 scientific categories,
3 difficulty levels, streak bonuses, and persistent score history.
"""

import json
import csv
import random
import sys
import os
from datetime import datetime


# ── ANSI colour helpers ────────────────────────────────────────────────────────
RESET  = "\033[0m"
BOLD   = "\033[1m"
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
MAGENTA= "\033[95m"
BLUE   = "\033[94m"
DIM    = "\033[2m"

CATEGORY_COLOURS = {
    "Química":        CYAN,
    "Física":         BLUE,
    "Matemáticas":    MAGENTA,
    "Informática / IA": GREEN,
    "Biología":       YELLOW,
    "Astronomía":     "\033[38;5;208m",   # orange
}

DIFFICULTY_POINTS = {"easy": 1, "medium": 2, "hard": 3}
HISTORY_FILE = "score_history.csv"
QUESTIONS_FILE = os.path.join(os.path.dirname(__file__), "questions.json")


# ═══════════════════════════════════════════════════════════════════════════════
# CORE FUNCTIONS (must be at module level, tested with pytest)
# ═══════════════════════════════════════════════════════════════════════════════

def load_questions(filepath: str = QUESTIONS_FILE) -> list[dict]:
    """Load and return the list of question dicts from a JSON file.

    Args:
        filepath: Path to the JSON questions bank.

    Returns:
        List of question dictionaries.

    Raises:
        FileNotFoundError: if the JSON file does not exist.
        ValueError: if the file contains invalid JSON or wrong structure.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Questions file not found: {filepath}")
    with open(filepath, encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in {filepath}: {exc}") from exc
    if not isinstance(data, list) or not data:
        raise ValueError("Questions file must contain a non-empty JSON array.")
    return data


def calculate_score(base_points: int, streak: int, time_bonus: int = 0) -> int:
    """Calculate the score for a single correct answer.

    Formula:
        score = base_points × streak_multiplier + time_bonus
        streak_multiplier = 1 + 0.5 × floor(streak / 3)   (caps at 4×)

    Args:
        base_points:  Points for the difficulty level (easy=1, med=2, hard=3).
        streak:       Current consecutive-correct-answer streak.
        time_bonus:   Optional bonus points (reserved for future use).

    Returns:
        Integer score >= 0.

    Examples:
        >>> calculate_score(1, 0)
        1
        >>> calculate_score(2, 3)
        4
        >>> calculate_score(3, 6)
        9
    """
    if base_points < 0:
        raise ValueError("base_points must be non-negative.")
    if streak < 0:
        raise ValueError("streak must be non-negative.")
    multiplier = 1.0 + 0.5 * (streak // 3)
    multiplier = min(multiplier, 4.0)           # cap at 4×
    return int(base_points * multiplier) + time_bonus


def filter_questions(questions: list[dict],
                     categories: list[str] | None = None,
                     difficulty: str | None = None) -> list[dict]:
    """Return a filtered subset of questions.

    Args:
        questions:   Full question bank.
        categories:  List of category names to include (None = all).
        difficulty:  'easy', 'medium', or 'hard' (None = all).

    Returns:
        Filtered list of question dicts.

    Raises:
        ValueError: if difficulty is not a valid value.
    """
    valid_difficulties = {None, "easy", "medium", "hard"}
    if difficulty not in valid_difficulties:
        raise ValueError(f"difficulty must be one of {valid_difficulties}, got '{difficulty}'.")

    result = questions
    if categories:
        result = [q for q in result if q["category"] in categories]
    if difficulty:
        result = [q for q in result if q["difficulty"] == difficulty]
    return result


def save_score(player: str, score: int, total: int,
               category: str, difficulty: str,
               filepath: str = HISTORY_FILE) -> None:
    """Append a game result to the CSV history file.

    Args:
        player:     Player name.
        score:      Points earned.
        total:      Total questions answered.
        category:   Category label (or 'Mixed').
        difficulty: Difficulty label (or 'Mixed').
        filepath:   Path to the CSV history file.
    """
    file_exists = os.path.exists(filepath)
    with open(filepath, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["timestamp", "player", "score",
                           "questions", "category", "difficulty"]
        )
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "player":    player,
            "score":     score,
            "questions": total,
            "category":  category,
            "difficulty": difficulty,
        })


def load_history(filepath: str = HISTORY_FILE) -> list[dict]:
    """Load and return the score history from the CSV file.

    Args:
        filepath: Path to the CSV history file.

    Returns:
        List of row dicts, or empty list if file doesn't exist.
    """
    if not os.path.exists(filepath):
        return []
    with open(filepath, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def format_leaderboard(history: list[dict], top_n: int = 5) -> str:
    """Build a formatted leaderboard string from history records.

    Args:
        history: List of score dicts from load_history().
        top_n:   Number of top entries to display.

    Returns:
        Multi-line string with the leaderboard table.
    """
    if not history:
        return "No hay partidas registradas todavía."

    sorted_history = sorted(history, key=lambda r: int(r["score"]), reverse=True)
    top = sorted_history[:top_n]

    medals = ["🥇", "🥈", "🥉"] + ["  " for _ in range(top_n)]
    lines = [f"\n{'─'*52}", f"  {'LEADERBOARD':^48}", f"{'─'*52}"]
    for i, row in enumerate(top):
        lines.append(
            f"  {medals[i]}  {row['player']:<16} {int(row['score']):>5} pts"
            f"   {row['timestamp']}"
        )
    lines.append(f"{'─'*52}")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# UI HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def clear():
    os.system("cls" if os.name == "nt" else "clear")


def banner():
    print(f"""
{CYAN}{BOLD}
  ╔═══════════════════════════════════════╗
  ║   🔬  S C I Q U I Z   P R O  🔭     ║
  ║     Trivia Científica Interactiva     ║
  ╚═══════════════════════════════════════╝
{RESET}""")


def choose_from_menu(options: list[str], prompt: str = "Elige una opción") -> int:
    """Show a numbered menu and return the 0-based index chosen."""
    for i, opt in enumerate(options, 1):
        print(f"  {BOLD}[{i}]{RESET} {opt}")
    while True:
        raw = input(f"\n{YELLOW}→ {prompt}: {RESET}").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return int(raw) - 1
        print(f"{RED}  Por favor introduce un número entre 1 y {len(options)}.{RESET}")


def ask_category_difficulty() -> tuple[list[str] | None, str | None]:
    """Interactive menus to select category and difficulty."""
    all_categories = [
        "Química", "Física", "Matemáticas",
        "Informática / IA", "Biología", "Astronomía"
    ]

    print(f"\n{BOLD}━━━ CATEGORÍA ━━━{RESET}")
    cat_options = ["Todas las categorías"] + all_categories
    cat_idx = choose_from_menu(cat_options, "Elige categoría")
    categories = None if cat_idx == 0 else [all_categories[cat_idx - 1]]

    print(f"\n{BOLD}━━━ DIFICULTAD ━━━{RESET}")
    diff_options = ["Mixta (todas)", "Fácil", "Media", "Difícil"]
    diff_idx = choose_from_menu(diff_options, "Elige dificultad")
    difficulty_map = {0: None, 1: "easy", 2: "medium", 3: "hard"}
    difficulty = difficulty_map[diff_idx]

    print(f"\n{BOLD}━━━ NÚMERO DE PREGUNTAS ━━━{RESET}")
    num_options = ["5 preguntas", "10 preguntas", "15 preguntas", "20 preguntas"]
    num_map = {0: 5, 1: 10, 2: 15, 3: 20}
    num_idx = choose_from_menu(num_options, "¿Cuántas preguntas?")
    num_questions = num_map[num_idx]

    return categories, difficulty, num_questions


def display_question(q: dict, number: int, total: int,
                     score: int, streak: int) -> None:
    """Print a question with its shuffled options."""
    cat_colour = CATEGORY_COLOURS.get(q["category"], CYAN)
    diff_symbol = {"easy": "⬡", "medium": "⬢", "hard": "⬛"}.get(q["difficulty"], "?")
    diff_colour = {"easy": GREEN, "medium": YELLOW, "hard": RED}.get(q["difficulty"], RESET)

    print(f"\n{DIM}{'─'*56}{RESET}")
    print(
        f"  {cat_colour}{BOLD}{q['category']}{RESET}   "
        f"{diff_colour}{diff_symbol} {q['difficulty'].upper()}{RESET}   "
        f"{DIM}Pregunta {number}/{total}   "
        f"Puntos: {score}   Racha: {streak}🔥{RESET}"
    )
    print(f"{DIM}{'─'*56}{RESET}")
    print(f"\n  {BOLD}{q['question']}{RESET}\n")

    letters = ["A", "B", "C", "D"]
    options = q["options"][:]
    random.shuffle(options)
    for letter, opt in zip(letters, options):
        print(f"    {CYAN}[{letter}]{RESET} {opt}")
    return options          # shuffled options, needed to check answer


def get_answer(options: list[str]) -> str:
    """Prompt the player for A/B/C/D and return the chosen option text."""
    valid = {"A", "B", "C", "D", "a", "b", "c", "d"}
    while True:
        raw = input(f"\n{YELLOW}→ Tu respuesta: {RESET}").strip().upper()
        if raw in {"A", "B", "C", "D"}:
            return options[ord(raw) - ord("A")]
        print(f"{RED}  Introduce A, B, C o D.{RESET}")


# ═══════════════════════════════════════════════════════════════════════════════
# GAME LOOP
# ═══════════════════════════════════════════════════════════════════════════════

def run_game(player: str, questions_bank: list[dict]) -> None:
    """Run one full game session for a player."""
    clear()
    banner()

    categories, difficulty, num_questions = ask_category_difficulty()

    pool = filter_questions(questions_bank, categories, difficulty)
    if not pool:
        print(f"{RED}No hay preguntas para esa combinación de categoría/dificultad.{RESET}")
        return

    if len(pool) < num_questions:
        print(
            f"{YELLOW}  Solo hay {len(pool)} preguntas disponibles para esta combinación."
            f" Usaremos todas.{RESET}"
        )
        num_questions = len(pool)

    selected = random.sample(pool, num_questions)

    score = 0
    streak = 0
    correct_count = 0

    for i, q in enumerate(selected, 1):
        clear()
        banner()
        shuffled_opts = display_question(q, i, num_questions, score, streak)
        chosen = get_answer(shuffled_opts)

        if chosen == q["answer"]:
            base = DIFFICULTY_POINTS[q["difficulty"]]
            earned = calculate_score(base, streak)
            streak += 1
            score += earned
            correct_count += 1
            print(f"\n  {GREEN}{BOLD}✔ ¡CORRECTO!{RESET} +{earned} puntos", end="")
            if streak > 1:
                print(f"  {YELLOW}(Racha: {streak} 🔥){RESET}", end="")
            print()
        else:
            streak = 0
            print(f"\n  {RED}{BOLD}✘ Incorrecto.{RESET} La respuesta era: {BOLD}{q['answer']}{RESET}")

        print(f"  {DIM}💡 {q['explanation']}{RESET}")
        input(f"\n  {DIM}[Pulsa ENTER para continuar]{RESET}")

    # ── End of game summary ────────────────────────────────────────────────────
    clear()
    banner()
    cat_label  = categories[0] if categories and len(categories) == 1 else "Mixta"
    diff_label = difficulty if difficulty else "Mixta"

    pct = round(correct_count / num_questions * 100)
    grade = (
        "🏆 ¡Sobresaliente!" if pct >= 90 else
        "🎉 Notable"         if pct >= 75 else
        "👍 Aprobado"        if pct >= 50 else
        "📚 Sigue practicando"
    )

    print(f"\n{BOLD}{'═'*52}{RESET}")
    print(f"{BOLD}  RESULTADO FINAL — {player}{RESET}")
    print(f"{'═'*52}")
    print(f"  Correctas : {GREEN}{correct_count}{RESET}/{num_questions}  ({pct}%)")
    print(f"  Puntuación: {CYAN}{BOLD}{score}{RESET} puntos")
    print(f"  Categoría : {cat_label}   Dificultad: {diff_label}")
    print(f"  {grade}")
    print(f"{'═'*52}\n")

    save_score(player, score, num_questions, cat_label, diff_label)
    print(f"  {DIM}Resultado guardado en {HISTORY_FILE}{RESET}\n")


def show_history_menu(player: str) -> None:
    """Display leaderboard and the player's personal history."""
    history = load_history()
    print(format_leaderboard(history))

    personal = [r for r in history if r["player"] == player]
    if personal:
        print(f"\n  {BOLD}Tus últimas partidas, {player}:{RESET}")
        for row in personal[-5:]:
            print(
                f"    {DIM}{row['timestamp']}{RESET}  "
                f"{CYAN}{row['score']} pts{RESET}  "
                f"{row['category']} / {row['difficulty']}"
            )
    input(f"\n  {DIM}[Pulsa ENTER para volver]{RESET}")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """Entry point: show the main menu and dispatch to game/history/exit."""
    clear()
    banner()

    # Load questions once
    try:
        questions_bank = load_questions()
    except (FileNotFoundError, ValueError) as exc:
        sys.exit(f"{RED}Error cargando preguntas: {exc}{RESET}")

    # Ask for player name
    player = input(f"{BOLD}  ¿Cómo te llamas, científico/a? {RESET}").strip()
    if not player:
        player = "Anónimo"

    while True:
        clear()
        banner()
        print(f"  Bienvenido/a, {CYAN}{BOLD}{player}{RESET}! ¿Qué quieres hacer?\n")
        options = [
            "🎮  Jugar una partida",
            "🏆  Ver historial y leaderboard",
            "🚪  Salir",
        ]
        choice = choose_from_menu(options, "Elige")

        if choice == 0:
            run_game(player, questions_bank)
        elif choice == 1:
            show_history_menu(player)
        else:
            clear()
            print(f"\n  {CYAN}{BOLD}¡Hasta la próxima, {player}! Sigue aprendiendo. 🔬{RESET}\n")
            sys.exit(0)


if __name__ == "__main__":
    main()
