"""Exercise Type 1: Explain It Cold.

Cognitive target: Retrieval practice, knowledge organization.
The user must explain a concept from scratch with no references.
"""

from typing import Optional

from mental_gym.exercises.base import difficulty_instruction


class ExplainExercise:
    name = "Explain It Cold"
    slug = "explain"

    def generation_prompt(self, topic_name: str, topic_description: str,
                          difficulty: int, domain: str,
                          mastery_notes: str = "",
                          kb_excerpt: str = "",
                          secondary_topic: Optional[str] = None) -> tuple[str, str]:
        system = f"""You are an expert trainer in {domain}, designing exercises to build genuine expertise.
You are creating an "Explain It Cold" exercise: the student must explain a concept from scratch with no references.

{difficulty_instruction(difficulty)}

Respond with valid JSON only. No markdown fences, no explanation outside the JSON."""

        user = f"""Create an "Explain It Cold" exercise on the topic: {topic_name}
Topic description: {topic_description}

{f"Knowledge base excerpt: {kb_excerpt}" if kb_excerpt else ""}
{f"Recent mastery observations for this student on this topic: {mastery_notes}" if mastery_notes else ""}

Generate a specific, focused question that tests genuine understanding — not a vague "explain X" but something that requires the student to demonstrate they understand the mechanism, significance, or implications.

Return JSON:
{{
  "prompt": "The specific question to ask the student",
  "key_points": ["Point 1 the answer should cover", "Point 2", "Point 3"]
}}"""

        return system, user

    def evaluation_prompt(self, exercise_prompt: str, user_response: str,
                          key_points: list[str], domain: str,
                          mastery_notes: str = "") -> tuple[str, str]:
        system = f"""You are a strict but constructive evaluator of {domain} knowledge.
You are evaluating a student's response to an "Explain It Cold" exercise.

Be honest and specific. If the answer is wrong, say so directly. Do not be encouraging
when the content is incorrect. Award scores that reflect actual quality:
- 1: Fundamentally wrong or empty
- 2: Shows awareness but major errors or omissions
- 3: Basically correct but missing important nuances
- 4: Good understanding with minor gaps
- 5: Expert-level explanation

Respond with valid JSON only. No markdown fences."""

        kp_str = "\n".join(f"- {p}" for p in key_points)
        user = f"""The student was asked:
{exercise_prompt}

Expected key points:
{kp_str}

Student's response:
{user_response}

{f"Previous mastery observations for context: {mastery_notes}" if mastery_notes else ""}

Evaluate the response. Return JSON:
{{
  "accuracy": <1-5>,
  "completeness": <1-5>,
  "depth": <1-5>,
  "feedback": "Specific constructive feedback. Say exactly what was wrong, missing, or imprecise. If correct, note what was done well and what could go deeper.",
  "mastery_observations": [
    {{"type": "demonstrated|missed|misconception|partial", "concept": "specific sub-concept", "detail": "what the student got right/wrong"}}
  ]
}}"""

        return system, user
