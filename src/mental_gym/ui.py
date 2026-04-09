"""Terminal I/O: prompts, colors, multi-line input collection."""

import os
import subprocess
import sys
import tempfile


# ANSI color codes
class Color:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"


def bold(text: str) -> str:
    return f"{Color.BOLD}{text}{Color.RESET}"


def dim(text: str) -> str:
    return f"{Color.DIM}{text}{Color.RESET}"


def colored(text: str, color: str) -> str:
    return f"{color}{text}{Color.RESET}"


def print_header(text: str):
    """Print a section header."""
    print(f"\n{Color.BOLD}{Color.CYAN}{text}{Color.RESET}")


def print_separator():
    print(colored("━" * 50, Color.DIM))


def print_exercise_header(exercise_num: int, total: int, phase: str,
                          exercise_type: str, topic_name: str):
    """Print the header for an exercise."""
    phase_colors = {
        "warmup": Color.YELLOW,
        "main": Color.BLUE,
        "cooldown": Color.MAGENTA,
        "review": Color.CYAN,
    }
    phase_color = phase_colors.get(phase, Color.WHITE)
    print()
    print_separator()
    print(
        f"{Color.BOLD}Exercise {exercise_num}/{total}{Color.RESET} "
        f"— {colored(phase.upper(), phase_color)} "
        f"— {colored(exercise_type, Color.CYAN)}"
    )
    print(f"Topic: {bold(topic_name)}")
    print()


def print_prompt(prompt_text: str):
    """Print the exercise prompt/question."""
    print(f"  {Color.WHITE}{prompt_text}{Color.RESET}")
    print()


def print_feedback(score_accuracy: float, score_completeness: float,
                   score_depth: float, overall: float, feedback: str):
    """Print evaluation feedback."""
    print()
    print_separator()

    def score_color(s):
        if s >= 4:
            return Color.GREEN
        elif s >= 3:
            return Color.YELLOW
        else:
            return Color.RED

    print(
        f"  Accuracy:     {colored(f'{score_accuracy:.1f}', score_color(score_accuracy))}/5  "
        f"  Completeness: {colored(f'{score_completeness:.1f}', score_color(score_completeness))}/5  "
        f"  Depth:        {colored(f'{score_depth:.1f}', score_color(score_depth))}/5"
    )
    print(f"  {bold('Overall:')}      {colored(f'{overall:.1f}', score_color(overall))}/5")
    print()
    print(f"  {Color.WHITE}{feedback}{Color.RESET}")
    print()


def print_session_summary(session_num: int, exercises_done: int,
                          avg_score: float, duration_seconds: int,
                          topic_deltas: dict):
    """Print end-of-session summary."""
    print()
    print(colored("━" * 50, Color.CYAN))
    print(bold(f"  Session #{session_num} Complete"))
    print(colored("━" * 50, Color.CYAN))
    mins = duration_seconds // 60
    secs = duration_seconds % 60
    print(f"  Exercises: {exercises_done}  |  Avg Score: {avg_score:.1f}/5  |  Time: {mins}m {secs}s")
    if topic_deltas:
        print()
        print(bold("  Mastery Changes:"))
        for topic_name, (old, new) in topic_deltas.items():
            delta = new - old
            arrow = colored("▲", Color.GREEN) if delta > 0 else colored("▼", Color.RED)
            print(f"    {arrow} {topic_name}: {old:.0%} → {new:.0%}")
    print()


def collect_response() -> str:
    """Collect multi-line user response. Submit with blank line (Enter twice)."""
    print(dim("  Your answer (press Enter twice on empty line to submit):"))
    lines = []
    try:
        while True:
            line = input("  > ")
            if line == "" and lines and lines[-1] == "":
                # Two blank lines = submit
                lines.pop()  # remove trailing blank
                break
            lines.append(line)
    except EOFError:
        pass

    return "\n".join(lines).strip()


def collect_response_editor(prompt_text: str = "") -> str:
    """Collect response via $EDITOR. Opens a temp file with the prompt as a comment."""
    editor = os.environ.get("EDITOR", "vim")
    header = f"# Write your response below. Lines starting with # are ignored.\n# Prompt: {prompt_text}\n\n"

    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(header)
        tmp_path = f.name

    try:
        subprocess.run([editor, tmp_path], check=True)
        with open(tmp_path) as f:
            lines = f.readlines()
        # Strip comment lines
        content = "".join(l for l in lines if not l.startswith("#"))
        return content.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        print_error(f"Could not open editor '{editor}'. Falling back to inline input.")
        return collect_response()
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def confirm(prompt: str, default: bool = True) -> bool:
    """Ask user yes/no confirmation."""
    suffix = " [Y/n] " if default else " [y/N] "
    try:
        response = input(prompt + suffix).strip().lower()
    except (EOFError, KeyboardInterrupt):
        return default
    if not response:
        return default
    return response in ("y", "yes")


def print_error(msg: str):
    print(f"{Color.RED}Error: {msg}{Color.RESET}")


def print_success(msg: str):
    print(f"{Color.GREEN}{msg}{Color.RESET}")


def print_info(msg: str):
    print(f"{Color.DIM}{msg}{Color.RESET}")
