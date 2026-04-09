"""Exercise Type 5: Teach the Confused Student.

Cognitive target: The protégé effect — teaching forces deep processing.
AI plays a smart but confused colleague with realistic misconceptions.
User must identify the misconception and correct it clearly.

This exercise is multi-turn: the AI presents confusion, user corrects,
AI pushes back with follow-up confusion.
"""

from typing import Optional

from mental_gym.exercises.base import difficulty_instruction


class TeachExercise:
    name = "Teach the Confused Student"
    slug = "teach"
    multi_turn = True  # Signals the trainer to use conversation mode

    def generation_prompt(self, topic_name: str, topic_description: str,
                          difficulty: int, domain: str,
                          mastery_notes: str = "",
                          kb_excerpt: str = "",
                          secondary_topic: Optional[str] = None) -> tuple[str, str]:
        system = f"""You are an expert trainer in {domain}, designing exercises to build genuine expertise.
You are creating a "Teach the Confused Student" exercise: you will play a smart but confused
colleague who has a specific, realistic misconception about a topic. The student must identify
what's wrong with your reasoning and correct it.

{difficulty_instruction(difficulty)}

The misconception should be:
- Realistic (something a smart person might actually believe)
- Specific (not vaguely wrong, but wrong in a precise way)
- Related to common misunderstandings in the field
- Plausible enough that a superficial correction won't suffice

Respond with valid JSON only. No markdown fences."""

        user = f"""Create a "Teach the Confused Student" exercise on: {topic_name}
Topic description: {topic_description}

{f"Knowledge base excerpt: {kb_excerpt}" if kb_excerpt else ""}
{f"Recent mastery observations: {mastery_notes}" if mastery_notes else ""}

Design a confused colleague's statement that contains a specific misconception.
The statement should sound reasonable on the surface but be wrong in an important way.

Also prepare a follow-up confusion that tests whether the student's correction
was deep enough — if they give a superficial fix, the follow-up should expose that.

Return JSON:
{{
  "prompt": "The confused colleague's statement, starting with 'So from what I understand...' or similar",
  "key_points": ["What the misconception is", "Why it's wrong", "What the correct understanding is"],
  "followup": "A follow-up question/confusion to push back after the student's first correction"
}}"""

        return system, user

    def evaluation_prompt(self, exercise_prompt: str, user_response: str,
                          key_points: list[str], domain: str,
                          mastery_notes: str = "") -> tuple[str, str]:
        system = f"""You are evaluating a student's ability to teach and correct misconceptions in {domain}.

Score based on:
- Did they correctly identify the misconception? (not just notice something is off)
- Was their correction accurate and complete?
- Did they explain WHY the misconception is wrong, not just state what's right?
- Was their explanation clear enough that the confused colleague would actually understand?

A student who says "that's wrong, the right answer is X" without explaining why gets a 2-3.
A student who identifies the specific flaw in reasoning and explains the correct mental model gets a 4-5.

Respond with valid JSON only. No markdown fences."""

        kp_str = "\n".join(f"- {p}" for p in key_points)
        user = f"""The confused colleague said:
{exercise_prompt}

The misconception and correct understanding:
{kp_str}

Student's correction:
{user_response}

{f"Previous mastery observations: {mastery_notes}" if mastery_notes else ""}

Evaluate the correction. Return JSON:
{{
  "accuracy": <1-5>,
  "completeness": <1-5>,
  "depth": <1-5>,
  "feedback": "Did the student identify the specific misconception? Was their explanation clear and correct? What did they miss?",
  "mastery_observations": [
    {{"type": "demonstrated|missed|misconception|partial", "concept": "specific teaching concept", "detail": "what this reveals about their understanding"}}
  ]
}}"""

        return system, user
