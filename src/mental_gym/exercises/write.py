"""Exercise Type 6: Write It From Scratch.

Cognitive target: Generative fluency, the ultimate test.
User writes a paragraph or section cold, no references.
AI evaluates substance (correctness, completeness, understanding), not style.
"""

from typing import Optional

from mental_gym.exercises.base import difficulty_instruction


class WriteExercise:
    name = "Write It From Scratch"
    slug = "write"
    use_editor = True  # Signals the trainer to offer $EDITOR mode

    def generation_prompt(self, topic_name: str, topic_description: str,
                          difficulty: int, domain: str,
                          mastery_notes: str = "",
                          kb_excerpt: str = "",
                          secondary_topic: Optional[str] = None) -> tuple[str, str]:
        system = f"""You are an expert trainer in {domain}, designing exercises to build genuine expertise.
You are creating a "Write It From Scratch" exercise: the student must write a paragraph
or short section (100-300 words) on a specific prompt, with no references. You evaluate
the SUBSTANCE — correctness, completeness, understanding — not the prose style.

{difficulty_instruction(difficulty)}

The writing prompt should be specific enough that vague generalities fail, but open enough
that the student must organize their knowledge and make choices about what to include.

Respond with valid JSON only. No markdown fences."""

        user = f"""Create a "Write It From Scratch" exercise on: {topic_name}
Topic description: {topic_description}

{f"Knowledge base excerpt: {kb_excerpt}" if kb_excerpt else ""}
{f"Recent mastery observations: {mastery_notes}" if mastery_notes else ""}

Design a writing prompt that tests whether the student can produce expert-level content
from memory. Good prompts include:
- "Write a Related Work paragraph positioning X against Y and Z"
- "Write a 200-word methodology sketch for studying X"
- "Draft an introduction paragraph that motivates why X matters"
- "Write a critique of approach X, covering its main limitations"

Return JSON:
{{
  "prompt": "The specific writing prompt, including approximate word count target",
  "key_points": ["Substantive point the writing should cover", "Another key point", "Important nuance"]
}}"""

        return system, user

    def evaluation_prompt(self, exercise_prompt: str, user_response: str,
                          key_points: list[str], domain: str,
                          mastery_notes: str = "") -> tuple[str, str]:
        system = f"""You are evaluating a student's written output in {domain}.
Focus on SUBSTANCE, not style. You are checking whether the content is:
- Factually correct (no errors, no made-up citations)
- Complete (covers the key points a knowledgeable person would include)
- Shows genuine understanding (not just buzzword assembly)
- Appropriately nuanced (acknowledges limitations, tensions, open questions)

Do NOT evaluate:
- Prose quality, grammar, or elegance
- Citation formatting
- Whether it reads like a published paper

A well-organized but factually shallow response gets a 2-3.
A messy but substantively deep and correct response gets a 4-5.

Respond with valid JSON only. No markdown fences."""

        kp_str = "\n".join(f"- {p}" for p in key_points)
        user = f"""The student was asked to write:
{exercise_prompt}

Expected substantive content:
{kp_str}

Student's writing:
{user_response}

{f"Previous mastery observations: {mastery_notes}" if mastery_notes else ""}

Evaluate the substance. Return JSON:
{{
  "accuracy": <1-5>,
  "completeness": <1-5>,
  "depth": <1-5>,
  "feedback": "Assess factual correctness, coverage of key points, and depth of understanding. Note specific errors, omissions, or insights.",
  "mastery_observations": [
    {{"type": "demonstrated|missed|misconception|partial", "concept": "specific concept", "detail": "what the writing reveals about their understanding"}}
  ]
}}"""

        return system, user
