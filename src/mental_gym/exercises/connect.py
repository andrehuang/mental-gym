"""Exercise Type 3: Connect the Dots.

Cognitive target: Relational knowledge, seeing the field as a network.
The user must articulate the relationship between two concepts.
"""

from typing import Optional

from mental_gym.exercises.base import difficulty_instruction


class ConnectExercise:
    name = "Connect the Dots"
    slug = "connect"

    def generation_prompt(self, topic_name: str, topic_description: str,
                          difficulty: int, domain: str,
                          mastery_notes: str = "",
                          kb_excerpt: str = "",
                          secondary_topic: Optional[str] = None) -> tuple[str, str]:
        system = f"""You are an expert trainer in {domain}, designing exercises to build genuine expertise.
You are creating a "Connect the Dots" exercise: the student must articulate the relationship,
tension, or connection between two concepts that are not obviously linked.

{difficulty_instruction(difficulty)}

The best connections are non-obvious but genuine. Avoid trivial "both are about X" connections.
Push for connections that reveal structural insights about the field.

Respond with valid JSON only. No markdown fences."""

        second = f" and {secondary_topic}" if secondary_topic else ""
        user = f"""Create a "Connect the Dots" exercise linking: {topic_name}{second}
Topic description: {topic_description}

{f"The second concept to connect is: {secondary_topic}" if secondary_topic else "Pick a second concept from the field that has a non-obvious but real connection to this topic."}
{f"Knowledge base excerpt: {kb_excerpt}" if kb_excerpt else ""}
{f"Recent mastery observations: {mastery_notes}" if mastery_notes else ""}

Ask the student to articulate the relationship between the two concepts. The question
should push for specifics: are they the same problem? Different manifestations of one problem?
Does one inform the other? Is there a tension?

Return JSON:
{{
  "prompt": "What is the relationship between [concept A] and [concept B]? Are they... Does one...",
  "key_points": ["Key connection 1", "Important nuance or tension", "Why this connection matters"]
}}"""

        return system, user

    def evaluation_prompt(self, exercise_prompt: str, user_response: str,
                          key_points: list[str], domain: str,
                          mastery_notes: str = "") -> tuple[str, str]:
        system = f"""You are evaluating a student's ability to connect concepts in {domain}.

Score based on whether the connection is:
- Genuine (not forced or superficial)
- Specific (identifies concrete shared mechanisms, tensions, or implications)
- Insightful (reveals something non-obvious about the field structure)
- Complete (covers the major aspects of the relationship)

A vague "both relate to X" deserves a 2. A specific structural insight deserves a 4-5.

Respond with valid JSON only. No markdown fences."""

        kp_str = "\n".join(f"- {p}" for p in key_points)
        user = f"""The student was asked:
{exercise_prompt}

Expected key connections:
{kp_str}

Student's response:
{user_response}

{f"Previous mastery observations: {mastery_notes}" if mastery_notes else ""}

Evaluate. Return JSON:
{{
  "accuracy": <1-5>,
  "completeness": <1-5>,
  "depth": <1-5>,
  "feedback": "Assess the connection. Note what was insightful, what was superficial, and what key connections were missed.",
  "mastery_observations": [
    {{"type": "demonstrated|missed|misconception|partial", "concept": "specific relational concept", "detail": "what this reveals about their field understanding"}}
  ]
}}"""

        return system, user
