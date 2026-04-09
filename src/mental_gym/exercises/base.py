"""Exercise type base protocol."""

from typing import Protocol, Optional


class ExerciseType(Protocol):
    """Protocol that all exercise types must implement."""

    name: str  # e.g., "Explain It Cold"
    slug: str  # e.g., "explain"

    def generation_prompt(self, topic_name: str, topic_description: str,
                          difficulty: int, domain: str,
                          mastery_notes: str = "",
                          kb_excerpt: str = "",
                          secondary_topic: Optional[str] = None) -> tuple[str, str]:
        """Return (system_prompt, user_prompt) to generate an exercise.

        The LLM response should be JSON with:
        - "prompt": the question to present to the user
        - "key_points": list of expected answer points (rubric for evaluation)
        """
        ...

    def evaluation_prompt(self, exercise_prompt: str, user_response: str,
                          key_points: list[str], domain: str,
                          mastery_notes: str = "") -> tuple[str, str]:
        """Return (system_prompt, user_prompt) to evaluate the user's response.

        The LLM response should be JSON with:
        - "accuracy": 1-5
        - "completeness": 1-5
        - "depth": 1-5
        - "feedback": specific constructive feedback
        - "mastery_observations": list of {"type", "concept", "detail"}
        """
        ...


DIFFICULTY_LABELS = {
    1: "Recall",
    2: "Comprehension",
    3: "Application",
    4: "Analysis",
    5: "Synthesis",
    6: "Evaluation",
}


def difficulty_instruction(level: int) -> str:
    """Return difficulty-level instruction for exercise generation."""
    label = DIFFICULTY_LABELS.get(level, "Recall")
    instructions = {
        1: "Ask a straightforward recall question. The student should demonstrate they know basic facts and terminology.",
        2: "Ask the student to explain a concept and why it matters. They should show understanding, not just recall.",
        3: "Present a scenario and ask how the concept applies. The student must transfer knowledge to a new situation.",
        4: "Ask the student to compare, contrast, or analyze. They should identify relationships, tensions, and nuances.",
        5: "Ask the student to synthesize multiple ideas into a coherent proposal or framework. This requires creative integration.",
        6: "Ask the student to evaluate a claim, assess validity, or critique an approach. This requires mature expert judgment.",
    }
    return f"Difficulty level: {level} ({label}). {instructions.get(level, instructions[1])}"
