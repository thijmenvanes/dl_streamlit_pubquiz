import streamlit as st
import requests
import datetime


# ---------------------------------------------------------------------------
# Lingo / Wordle game constants and logic
# ---------------------------------------------------------------------------
VALID_WORDS = {"diner", "trein", "kater", "boter", "water", "loper", "hater"}
VALID_6_LETTER_WORDS = {"zuiden", "buiten", "harten", "kijken", "lopen", "werken", "leren"}

SECRET_WORD: str = "diner"
MAX_ATTEMPTS: int = 8
WORD_LENGTH: int = 5
GAME_SCORE: int | None = None

GREEN_SQUARE: str = "🟩"
YELLOW_SQUARE: str = "🟨"
GRAY_SQUARE: str = "⬛"

TILE_CSS: str = """
    <style>
    .lingo-row {
        display: flex;
        gap: 0.4rem;
        margin-bottom: 0.4rem;
        justify-content: center;
    }
    .lingo-tile {
        width: 3rem;
        height: 3rem;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.5rem;
        font-weight: bold;
        color: white;
        border-radius: 0.4rem;
        text-transform: uppercase;
    }
    .lingo-tile.green { background-color: #6aaa64; }
    .lingo-tile.yellow { background-color: #c9b458; }
    .lingo-tile.gray { background-color: #787c7e; }
    </style>
"""


def _create_notion_row(
    team_name: str,
    start_time: datetime.datetime,
    notion_token: str,
    database_id: str,
) -> requests.Response:
    """Create a Notion database row with the team name and start time.

    Args:
        team_name: Name of the participating team.
        start_time: Timestamp when the team started the quiz.
        notion_token: Bearer token for the Notion integration.
        database_id: Identifier of the target Notion database.

    Returns:
        The HTTP response returned by the Notion API.
    """
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {notion_token}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }
    payload = {
        "parent": {"database_id": database_id},
        "properties": {
            "Team Name": {"title": [{"text": {"content": team_name}}]},
            "Start Time": {"date": {"start": start_time.isoformat()}},
        },
    }
    return requests.post(url=url, json=payload, headers=headers)


def _render_row(guess: str, feedback: list[str]) -> str:
    """Render a single guess as HTML tiles with colored letter blocks.

    Args:
        guess: The guessed word.
        feedback: List of emoji feedback strings per letter.

    Returns:
        HTML string representing the row of colored letter tiles.
    """
    color_map: dict[str, str] = {
        GREEN_SQUARE: "green",
        YELLOW_SQUARE: "yellow",
        GRAY_SQUARE: "gray",
    }
    tiles: list[str] = []
    for letter, emoji in zip(guess, feedback):
        color_class = color_map[emoji]
        tiles.append(
            f'<div class="lingo-tile {color_class}">{letter}</div>'
        )
    return f'<div class="lingo-row">{ "".join(tiles) }</div>'


def _calculate_score(attempts_needed: int | None) -> float | None:
    """Calculate the quiz score from the number of attempts needed.

    Args:
        attempts_needed: Number of attempts used to guess the word, or None
            if the word was not guessed.

    Returns:
        The score based on 4 - (attempts_needed - 1) * 0.5, or None when
        the word was not guessed.
    """
    if attempts_needed is None:
        return None
    return 4 - (attempts_needed - 1) * 0.5


class LingoGame:
    """Manages the state and feedback logic for a Dutch Lingo game."""

    def __init__(
        self,
        secret_word: str = SECRET_WORD,
        valid_words: set[str] | None = None,
        word_length: int = WORD_LENGTH,
        max_attempts: int = MAX_ATTEMPTS,
    ) -> None:
        """Initialize a new Lingo game with an empty guess history.

        Args:
            secret_word: The word the player must guess.
            valid_words: Set of allowed guess words. Defaults to VALID_WORDS.
            word_length: Required length of each guess.
            max_attempts: Maximum number of allowed guesses.
        """
        self.secret_word: str = secret_word.lower()
        self.valid_words: set[str] = valid_words or VALID_WORDS
        self.word_length: int = word_length
        self.max_attempts: int = max_attempts
        self.attempts: int = 0
        self.guesses: list[str] = []
        self.feedback_history: list[list[str]] = []
        self.completed: bool = False
        self.attempts_needed: int | None = None

    def validate_guess(self, guess: str) -> bool:
        """Check whether a guess is valid.

        Args:
            guess: The player's guessed word.

        Returns:
            True if the guess has the required length and is in valid_words.
        """
        return len(guess) == self.word_length and guess in self.valid_words

    def _calculate_feedback(self, guess: str) -> list[str]:
        """Calculate emoji feedback for a single guess.

        The algorithm first marks exact positional matches (green) and then
        marks remaining letters as yellow only when the secret word still has
        unmatched occurrences of that letter. This prevents double-counting.

        Args:
            guess: The player's guessed word.

        Returns:
            A list of emoji feedback strings, one per letter position.
        """
        feedback: list[str] = [GRAY_SQUARE] * self.word_length
        secret_remaining: list[str] = list(self.secret_word)

        for index, letter in enumerate(guess):
            if letter == self.secret_word[index]:
                feedback[index] = GREEN_SQUARE
                secret_remaining[index] = ""

        for index, letter in enumerate(guess):
            if feedback[index] == GREEN_SQUARE:
                continue
            if letter in secret_remaining:
                feedback[index] = YELLOW_SQUARE
                secret_remaining[secret_remaining.index(letter)] = ""

        return feedback

    def process_guess(self, guess: str) -> tuple[bool, str]:
        """Process a single guess and update game state.

        Args:
            guess: The player's guessed word.

        Returns:
            A tuple of (is_valid, message). When invalid, the message explains
            why and no attempt is consumed.
        """
        normalized_guess = guess.strip().lower()

        if not self.validate_guess(guess=normalized_guess):
            return False, (
                f"'{normalized_guess}' is geen geldig "
                f"{self.word_length}-letterwoord. Probeer opnieuw."
            )

        self.attempts += 1
        self.guesses.append(normalized_guess)
        feedback = self._calculate_feedback(guess=normalized_guess)
        self.feedback_history.append(feedback)

        if normalized_guess == self.secret_word:
            self.completed = True
            self.attempts_needed = self.attempts
            return True, (
                f"🎉 Gefeliciteerd! Je hebt het woord geraden in "
                f"{self.attempts} beurt(en)."
            )

        if self.attempts >= self.max_attempts:
            self.completed = True
            self.attempts_needed = None
            return True, (
                f"Helaas, je hebt geen pogingen meer. "
                f"Het woord was: {self.secret_word.upper()}"
            )

        return True, " "

    def get_feedback_grid(self) -> str:
        """Return an HTML string of all guesses as colored letter tiles.

        Returns:
            HTML showing each guess with letters inside colored blocks.
        """
        rows: list[str] = [TILE_CSS]
        for guess, feedback in zip(self.guesses, self.feedback_history):
            rows.append(_render_row(guess=guess, feedback=feedback))
        return "\n".join(rows)



# 1. Page Configuration (Forced centering for mobile optimization)
st.set_page_config(
    page_title="Datalab Pubquiz",
    layout="centered"
)

# 2. Securely Fetch Credentials
# Locally, these pull from .streamlit/secrets.toml
# In production, these pull from your Streamlit Cloud Dashboard settings
NOTION_TOKEN = st.secrets["NOTION_TOKEN"]
DATABASE_ID = st.secrets["DATABASE_ID"]

# 3. Track Session State (Prevents users from re-submitting if they refresh)
if "submitted" not in st.session_state:
    st.session_state.submitted = False

if "team_registered" not in st.session_state:
    st.session_state.team_registered = False

if "team_name" not in st.session_state:
    st.session_state.team_name = ""

if "start_time" not in st.session_state:
    st.session_state.start_time = None

if "show_question_3" not in st.session_state:
    st.session_state.show_question_3 = False

if "lingo_game" not in st.session_state:
    st.session_state.lingo_game = LingoGame()

if "show_question_4" not in st.session_state:
    st.session_state.show_question_4 = False

if "lingo_game_6" not in st.session_state:
    st.session_state.lingo_game_6 = LingoGame(
        secret_word="zuiden",
        valid_words=VALID_6_LETTER_WORDS,
        word_length=6,
    )

# App UI Header
st.title("🧠 Datalab Pubquiz")
st.subheader("Ronde 4: Lunchronde")

# 4. App Flow Control
if st.session_state.submitted:
    st.success("🎉 Je antwoorden zijn verzonden!")
    st.balloons()
elif not st.session_state.team_registered:
    st.write("### Laat weten wie je bent")
    team_name_input = st.text_input(
        label="Wat is de naam van je team?",
        value=st.session_state.team_name,
    )
    start_button = st.button(
        label="Oké, door!",
        use_container_width=True,
    )
    if start_button:
        if not team_name_input:
            st.error("⚠️ Geef je teamnaam op voordat je verdergaat!")
        else:
            start_time = datetime.datetime.now()
            response = _create_notion_row(
                team_name=team_name_input,
                start_time=start_time,
                notion_token=NOTION_TOKEN,
                database_id=DATABASE_ID,
            )
            if response.status_code == 200:
                st.session_state.team_name = team_name_input
                st.session_state.start_time = start_time
                st.session_state.team_registered = True
                st.rerun()
            else:
                st.error(
                    f"Notion API error ({response.status_code}): {response.text}"
                )
else:
    st.info(f"Team: **{st.session_state.team_name}**")

    # Everything inside st.form stays frozen until the user hits the submit button
    with st.form("quiz_form"):
        st.write("### Beantwoord de vragen")

        # Question 1 (Using mobile-friendly segmented controls)
        q1_ans = st.number_input(
            label="Beantwoord vraag 1 (wacht op de quizmaster)"
        )

        # Question 2
        q2_ans = st.number_input(
            label="Beantwoord vraag 2 (wacht op de quizmaster)"
        )

        st.divider()

        # Question 3: Lingo game reveal button
        st.write("### Vraag 3 (Wacht op de quizmaster)")
        if not st.session_state.show_question_3:
            show_q3 = st.form_submit_button(
                label="Toon vraag 3",
                use_container_width=True,
            )
            if show_q3:
                st.session_state.show_question_3 = True
                st.rerun()

        if st.session_state.show_question_3:
            game = st.session_state.lingo_game
            st.info("🎯 Raad het 5-letterige woord (maximaal 8 pogingen).")

            if not game.completed:
                guess = st.text_input(
                    label="Jouw gok:",
                    max_chars=5,
                    key=f"guess_input_{game.attempts}",
                ).strip().lower()
                guess_button = st.form_submit_button(
                    label="Controleer gok",
                    use_container_width=True,
                )
                if guess_button:
                    is_valid, message = game.process_guess(guess=guess)
                    if is_valid:
                        st.session_state.lingo_game = game
                        st.rerun()
                    else:
                        st.warning(message)

            if game.guesses:
                st.markdown(game.get_feedback_grid(), unsafe_allow_html=True)

            if game.completed:
                if game.attempts_needed is not None:
                    st.success(
                        f"🎉 Gefeliciteerd! Je hebt het woord geraden in "
                        f"{game.attempts_needed} beurt(en)."
                    )
                else:
                    st.error(
                        f"Helaas, je hebt geen pogingen meer. "
                        f"Het woord was: {game.secret_word.upper()}"
                    )

        st.divider()

        # Question 4: 6-letter Lingo game reveal button
        st.write("### Vraag 4 (Wacht op de quizmaster)")
        if not st.session_state.show_question_4:
            show_q4 = st.form_submit_button(
                label="Toon vraag 4",
                use_container_width=True,
            )
            if show_q4:
                st.session_state.show_question_4 = True
                st.rerun()

        if st.session_state.show_question_4:
            game_6 = st.session_state.lingo_game_6
            st.info("🎯 Raad het 6-letterige woord (maximaal 8 pogingen).")

            if not game_6.completed:
                guess_6 = st.text_input(
                    label="Jouw gok:",
                    max_chars=6,
                    key=f"guess_input_6_{game_6.attempts}",
                ).strip().lower()
                guess_button_6 = st.form_submit_button(
                    label="Controleer gok (6 letters)",
                    use_container_width=True,
                )
                if guess_button_6:
                    is_valid_6, message_6 = game_6.process_guess(guess=guess_6)
                    if is_valid_6:
                        st.session_state.lingo_game_6 = game_6
                        st.rerun()
                    else:
                        st.warning(message_6)

            if game_6.guesses:
                st.markdown(game_6.get_feedback_grid(), unsafe_allow_html=True)

            if game_6.completed:
                if game_6.attempts_needed is not None:
                    st.success(
                        f"🎉 Gefeliciteerd! Je hebt het woord geraden in "
                        f"{game_6.attempts_needed} beurt(en)."
                    )
                else:
                    st.error(
                        f"Helaas, je hebt geen pogingen meer. "
                        f"Het woord was: {game_6.secret_word.upper()}"
                    )

        st.divider()

        # Form Submission Button (stretching to full width makes it easier to tap on phones)
        submit_button = st.form_submit_button(
            label="Lock In Answers 🚀",
            use_container_width=True,
        )

        # 5. Submission Logic
        if submit_button:
            # Frontend validation checks
            if not q1_ans or not q2_ans:
                st.error("⚠️ Beantwoord alle vragen voordat je indient!")
            else:
                with st.spinner("Antwoorden worden verzonden naar de quizmaster..."):
                    # Map the form entries cleanly to Notion's exact database schema
                    payload = {
                        "parent": {"database_id": DATABASE_ID},
                        "properties": {
                            "Team Name": {
                                "title": [{"text": {"content": st.session_state.team_name}}]
                            },
                            "Q1 Answer": {
                                "number": q1_ans
                            },
                            "Q2 Answer": {
                                "number": q2_ans
                            },
                            "Score woord-5": {
                                "number": _calculate_score(st.session_state.lingo_game.attempts_needed)
                            },
                            "Score woord-6": {
                                "number": _calculate_score(st.session_state.lingo_game_6.attempts_needed)
                            }
                        }
                    }

                    try:
                        # Make the API call
                        response = requests.post(
                            url="https://api.notion.com/v1/pages",
                            json=payload,
                            headers={
                                "Authorization": f"Bearer {NOTION_TOKEN}",
                                "Content-Type": "application/json",
                                "Notion-Version": "2022-06-28",
                            },
                        )

                        if response.status_code == 200:
                            # Update state so the quiz vanishes and showing the success banner
                            st.session_state.submitted = True
                            st.rerun()
                        else:
                            st.error(f"Notion API error ({response.status_code}): {response.text}")
                    except Exception as e:
                        st.error(f"Failed to connect to Notion: {e}")