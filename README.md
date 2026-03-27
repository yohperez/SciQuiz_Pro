# SciQuiz Pro

#### Video Demo: <URL HERE>

#### Description:

SciQuiz Pro is a command-line trivia game focused on science, built in Python as the final project for CS50P. The game challenges players with questions across six scientific disciplines — Chemistry, Physics, Mathematics, Computer Science / AI, Biology, and Astronomy — with three difficulty levels, a streak-based bonus scoring system, and persistent score history saved to a local CSV file.

---

## Motivation

After completing the CS50P curriculum, I wanted to build something that combined two passions: science communication and clean software design. A trivia game felt like the perfect vehicle — simple enough to be approachable, yet with enough moving parts to exercise every concept covered in the course: file I/O, data structures, functions with well-defined contracts, unit testing, and a polished user-facing CLI.

---

## Project Structure

```
project/
├── project.py          ← Main program (main + core functions)
├── test_project.py     ← pytest test suite
├── questions.json      ← Question bank (36 questions, 6 categories)
├── requirements.txt    ← Python dependencies
├── score_history.csv   ← Created at runtime when the first game is saved
└── README.md           ← This file
```

---

## Files in Detail

### `project.py`

This is the heart of the application. It contains `main()` and all the required custom functions at module level (not nested). Here is a breakdown of every function:

**`load_questions(filepath)`**
Reads and validates the JSON question bank. It raises `FileNotFoundError` if the file is missing, and `ValueError` if the JSON is malformed or the array is empty. Returning a plain Python list of dictionaries makes the rest of the code agnostic to the storage format.

**`calculate_score(base_points, streak, time_bonus=0)`**
Computes the points earned for a single correct answer. The scoring formula rewards consecutive correct answers (streaks) with a multiplier that increases by 0.5× every 3 questions in a row, capping at 4×. This creates an exciting risk/reward dynamic: a hard question answered during a long streak is worth up to 12 points. The function raises `ValueError` for negative inputs and always returns an integer.

**`filter_questions(questions, categories=None, difficulty=None)`**
Pure filtering function: takes the full question bank and returns only the questions that match the chosen category list and/or difficulty string. Both parameters are optional (None = no filter). Raises `ValueError` for unrecognised difficulty strings. This design makes it trivially easy to add new filter criteria in the future.

**`save_score(player, score, total, category, difficulty, filepath)`**
Appends one row to the CSV history file, creating the file with a header row if it doesn't exist yet. Using `csv.DictWriter` guarantees that the column order is always consistent regardless of insertion order in the dict.

**`load_history(filepath)`**
Reads the CSV history file and returns a list of dicts. Returns an empty list (not an error) if the file does not exist yet, which keeps the calling code simple.

**`format_leaderboard(history, top_n=5)`**
Converts raw history records into a human-readable leaderboard string sorted by score (descending). Separating formatting from printing makes this function easy to test and reuse.

**`run_game(player, questions_bank)`**
The main game loop. It calls `ask_category_difficulty()` to collect the player's preferences, samples random questions from the filtered pool, renders each question with `display_question()`, collects the answer with `get_answer()`, updates the streak and score, and finally prints a summary screen with a performance grade before saving the result.

**`main()`**
Entry point. Loads the question bank, asks for the player's name, and drives a `while True` menu loop that lets the player start a game, view history, or exit cleanly.

The UI uses ANSI escape codes for coloured terminal output. Each scientific category has its own colour (cyan for Chemistry, blue for Physics, magenta for Mathematics, etc.), making the interface feel polished without any external library dependency.

### `test_project.py`

Contains 30 pytest tests organised into six groups, one per core function. Key design decisions:

- **Fixtures** (`sample_json`, `history_csv`) use `tmp_path` to create isolated temporary files, so tests never touch the real `questions.json` or `score_history.csv` and can run in any order without side effects.
- Tests cover both the **happy path** (expected inputs produce expected outputs) and **error paths** (invalid inputs raise the correct exception with a meaningful message).
- The `format_leaderboard` tests verify the *relative order* of entries rather than exact string formatting, making the tests robust to cosmetic changes in the output.

### `questions.json`

The question bank contains 36 questions: 6 questions per category × 6 categories, with 2 questions per difficulty level (easy, medium, hard) per category. Each question has five fields: `category`, `difficulty`, `question`, `options` (4 choices), `answer`, and `explanation`. The explanation is shown after every answer — correct or not — reinforcing learning rather than just keeping score.

The hard-level questions are deliberately challenging and include topics from university-level science: DFT/Kohn-Sham theory (Chemistry), the Lorentz-invariant spacetime interval (Physics), Weierstrass's extreme value theorem (Mathematics), the Transformer attention mechanism (AI), DNA ligase and epigenetic methylation (Biology), and Type Ia supernovae as evidence for dark energy (Astronomy).

### `requirements.txt`

The only external dependency is `pytest`, used exclusively for testing. The game itself runs on the Python standard library alone (`json`, `csv`, `os`, `sys`, `random`, `datetime`), making installation trivial and the project completely portable.

---

## How to Run

```bash
# Install dependencies
pip install -r requirements.txt

# Run the game
python project.py

# Run all tests
pytest test_project.py -v
```

---

## Design Decisions

**Why store history in CSV instead of JSON?**
CSV is the natural format for tabular, append-only data. It is human-readable, easily opened in Excel or LibreOffice, and trivially importable into pandas for further analysis — relevant given the scientific audience the game targets.

**Why cap the streak multiplier at 4×?**
Unlimited multipliers can make early-game performance irrelevant. A 4× cap means a perfect-streak player on hard questions earns 12 points per question — impressive but not astronomically ahead of a player with moderate streaks.

**Why shuffle answer options at display time rather than in the JSON?**
Storing the correct answer as a plain string (not an index) means the question bank is easy to read, edit, and extend by hand. Shuffling at display time with `random.shuffle()` also prevents players from memorising "the answer is always B" patterns across sessions.

**Why separate `format_leaderboard` from printing it?**
Pure functions — those that return a value rather than producing side effects — are dramatically easier to unit-test. By returning a string from `format_leaderboard`, the test can inspect its content with simple `assert "name" in result` checks without capturing stdout.

---

## Possible Extensions

- Add a timed mode (time pressure per question, with time_bonus feeding into `calculate_score`).
- Fetch additional questions dynamically from an API (e.g., the Open Trivia Database).
- Export the leaderboard to a styled HTML file.
- Add a `--category` and `--difficulty` CLI flag so the game can be launched non-interactively in scripts.

---

*This was CS50P. Thank you, David!*
