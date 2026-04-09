"""Exercise Type 4: Defend or Attack.

Cognitive target: Argumentation, understanding limitations, reviewer mindset.
The user steelmans or critiques a position; the AI plays the opposite role.
"""

from typing import Optional

from mental_gym.exercises.base import difficulty_instruction


class DefendExercise:
    name = "Defend or Attack"
    slug = "defend"

    def generation_prompt(self, topic_name: str, topic_description: str,
                          difficulty: int, domain: str,
                          mastery_notes: str = "",
                          kb_excerpt: str = "",
                          secondary_topic: Optional[str] = None) -> tuple[str, str]:
        system = f"""You are an expert trainer in {domain}, designing exercises to build genuine expertise.
You are creating a "Defend or Attack" exercise: present a claim or position from the field,
and ask the student to either defend (steelman) or attack (find weaknesses) it.

{difficulty_instruction(difficulty)}

Choose claims that are genuinely debatable — not obviously true or false. The best claims
are ones where smart people disagree. Alternate between asking students to defend and attack.

Respond with valid JSON only. No markdown fences."""

        user = f"""Create a "Defend or Attack" exercise related to: {topic_name}
Topic description: {topic_description}

{f"Knowledge base excerpt: {kb_excerpt}" if kb_excerpt else ""}
{f"Recent mastery observations: {mastery_notes}" if mastery_notes else ""}

Present a specific, debatable claim from this area of the field. Then ask the student
to either:
- DEFEND it (make the strongest possible case)
- ATTACK it (find the most compelling weaknesses)

Choose one direction. The claim should be specific enough that vague responses fail.

Return JSON:
{{
  "prompt": "The claim + whether to defend or attack it",
  "key_points": ["Strong argument for/against 1", "Strong argument 2", "Key nuance to address"]
}}"""

        return system, user

    def evaluation_prompt(self, exercise_prompt: str, user_response: str,
                          key_points: list[str], domain: str,
                          mastery_notes: str = "") -> tuple[str, str]:
        system = f"""You are evaluating a student's argumentation in {domain}.
After scoring, you will play the OPPOSITE role — if the student defended, you attack;
if they attacked, you defend. This forces engagement with both sides.

Score based on:
- Argument quality: specific, well-supported, not hand-wavy
- Completeness: addresses the strongest counterarguments
- Intellectual honesty: acknowledges limitations of their own position
- Sophistication: goes beyond surface-level pros/cons

Respond with valid JSON only. No markdown fences."""

        kp_str = "\n".join(f"- {p}" for p in key_points)
        user = f"""The student was asked:
{exercise_prompt}

Expected strong arguments:
{kp_str}

Student's response:
{user_response}

{f"Previous mastery observations: {mastery_notes}" if mastery_notes else ""}

Evaluate the argument. Then briefly play devil's advocate — present the strongest
counterargument to the student's position.

Return JSON:
{{
  "accuracy": <1-5>,
  "completeness": <1-5>,
  "depth": <1-5>,
  "feedback": "Assessment of argument quality. Then: 'Devil's advocate: [strongest counterargument]'. This pushes the student to think about both sides.",
  "mastery_observations": [
    {{"type": "demonstrated|missed|misconception|partial", "concept": "specific argumentation concept", "detail": "what this reveals about their analytical ability"}}
  ]
}}"""

        return system, user
