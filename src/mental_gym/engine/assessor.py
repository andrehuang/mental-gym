"""Evaluate user responses via LLM and parse structured scores."""

import json
from dataclasses import dataclass, field
from typing import List, Optional

from mental_gym.engine.llm import LLMBackend


@dataclass
class MasteryObservation:
    type: str  # "demonstrated" | "missed" | "misconception" | "partial"
    concept: str
    detail: str = ""


@dataclass
class EvaluationResult:
    accuracy: float
    completeness: float
    depth: float
    overall: float
    feedback: str
    mastery_observations: List[MasteryObservation] = field(default_factory=list)


def evaluate_response(llm: LLMBackend,
                      system_prompt: str,
                      user_prompt: str) -> EvaluationResult:
    """Send evaluation prompt to LLM and parse the structured response."""
    response = llm.complete(system_prompt, user_prompt, json_mode=True)

    # Parse JSON — handle markdown-wrapped responses
    text = response.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(l for l in lines if not l.strip().startswith("```"))

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # Retry with explicit JSON instruction
        retry_prompt = user_prompt + "\n\nIMPORTANT: Respond with valid JSON only."
        response = llm.complete(system_prompt, retry_prompt, json_mode=True)
        text = response.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(l for l in lines if not l.strip().startswith("```"))
        data = json.loads(text)

    # Extract scores with bounds checking
    def clamp(v, lo=1.0, hi=5.0):
        try:
            return max(lo, min(hi, float(v)))
        except (TypeError, ValueError):
            return 3.0

    accuracy = clamp(data.get("accuracy", 3))
    completeness = clamp(data.get("completeness", 3))
    depth = clamp(data.get("depth", 3))
    overall = round((accuracy + completeness + depth) / 3, 1)
    feedback = data.get("feedback", "No feedback provided.")

    # Parse mastery observations
    observations = []
    for obs in data.get("mastery_observations", []):
        if isinstance(obs, dict) and "concept" in obs:
            observations.append(MasteryObservation(
                type=obs.get("type", "partial"),
                concept=obs["concept"],
                detail=obs.get("detail", ""),
            ))

    return EvaluationResult(
        accuracy=accuracy,
        completeness=completeness,
        depth=depth,
        overall=overall,
        feedback=feedback,
        mastery_observations=observations,
    )


def generate_exercise(llm: LLMBackend,
                      system_prompt: str,
                      user_prompt: str) -> tuple[str, list[str]]:
    """Send generation prompt to LLM and parse the exercise.

    Returns (prompt_text, key_points).
    """
    response = llm.complete(system_prompt, user_prompt, json_mode=True)

    text = response.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(l for l in lines if not l.strip().startswith("```"))

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        retry_prompt = user_prompt + "\n\nIMPORTANT: Respond with valid JSON only."
        response = llm.complete(system_prompt, retry_prompt, json_mode=True)
        text = response.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(l for l in lines if not l.strip().startswith("```"))
        data = json.loads(text)

    prompt_text = data.get("prompt", "")
    key_points = data.get("key_points", [])

    if not prompt_text:
        raise ValueError("LLM returned empty exercise prompt")

    return prompt_text, key_points
