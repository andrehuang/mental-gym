"""Exercise Type 2: Predict Before You Read.

Cognitive target: Hypothesis generation, testing mental models.
The user predicts study findings before seeing them.
"""

from typing import Optional

from mental_gym.exercises.base import difficulty_instruction


class PredictExercise:
    name = "Predict Before You Read"
    slug = "predict"

    def generation_prompt(self, topic_name: str, topic_description: str,
                          difficulty: int, domain: str,
                          mastery_notes: str = "",
                          kb_excerpt: str = "",
                          secondary_topic: Optional[str] = None) -> tuple[str, str]:
        system = f"""You are an expert trainer in {domain}, designing exercises to build genuine expertise.
You are creating a "Predict Before You Read" exercise: present the setup of a study or experiment,
and ask the student to predict the findings BEFORE revealing them.

{difficulty_instruction(difficulty)}

The prediction error is where learning happens. Design scenarios where the outcome is
non-obvious and tests whether the student has accurate mental models of the field.

Respond with valid JSON only. No markdown fences."""

        user = f"""Create a "Predict Before You Read" exercise related to: {topic_name}
Topic description: {topic_description}

{f"Knowledge base excerpt: {kb_excerpt}" if kb_excerpt else ""}
{f"Recent mastery observations: {mastery_notes}" if mastery_notes else ""}

Present the setup of a real or realistic study/experiment in this area. Include:
- Research question or goal
- Method overview (enough to reason about outcomes)
- Ask the student to predict specific outcomes

Do NOT reveal the actual findings in the prompt — those go in key_points.

Return JSON:
{{
  "prompt": "Description of the study setup + 'What do you predict they found? Be specific about...'",
  "key_points": ["Actual finding 1", "Actual finding 2", "Why this outcome occurred"]
}}"""

        return system, user

    def evaluation_prompt(self, exercise_prompt: str, user_response: str,
                          key_points: list[str], domain: str,
                          mastery_notes: str = "") -> tuple[str, str]:
        system = f"""You are evaluating a student's prediction about a study in {domain}.

The goal is NOT whether they predicted correctly — it's whether their reasoning shows
a well-calibrated mental model. Good scores for:
- Predictions close to reality (accurate mental model)
- Specific, justified predictions (not vague hedging)
- Good reasoning even if the prediction was wrong
- Acknowledging uncertainty where appropriate

Score lower for:
- Wildly wrong predictions based on flawed models
- Vague or noncommittal responses
- Failure to engage with the specifics of the method

Respond with valid JSON only. No markdown fences."""

        kp_str = "\n".join(f"- {p}" for p in key_points)
        user = f"""The student was asked to predict the outcome of:
{exercise_prompt}

Actual findings (the key points):
{kp_str}

Student's prediction:
{user_response}

{f"Previous mastery observations: {mastery_notes}" if mastery_notes else ""}

Evaluate the prediction. After scoring, reveal the actual findings and explain the gap between prediction and reality.

Return JSON:
{{
  "accuracy": <1-5>,
  "completeness": <1-5>,
  "depth": <1-5>,
  "feedback": "Reveal actual findings. Explain where prediction matched or diverged, and what this tells the student about their mental model.",
  "mastery_observations": [
    {{"type": "demonstrated|missed|misconception|partial", "concept": "specific concept", "detail": "what this prediction reveals about their understanding"}}
  ]
}}"""

        return system, user
