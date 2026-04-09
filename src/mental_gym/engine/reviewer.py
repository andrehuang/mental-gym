"""Article/writing review — parse claims, generate challenge exercises."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from mental_gym.engine.llm import LLMBackend


@dataclass
class ArticleClaim:
    claim: str
    claim_type: str  # "empirical" | "theoretical" | "methodological" | "assumption"
    related_topics: List[str]  # topic IDs from the graph
    challenge_prompt: str  # the exercise prompt to present


def extract_claims_prompt(article_text: str, domain: str,
                          topic_ids: List[str]) -> tuple[str, str]:
    """Return (system, user) prompt to extract claims from an article."""

    system = f"""You are an expert in {domain} analyzing a piece of writing for claims,
arguments, and assumptions that should be stress-tested.

Your role is to identify the most important claims and generate targeted challenges.
Focus on claims that are:
- Central to the argument (not peripheral)
- Testable or debatable (not trivially true)
- Where the author might have blind spots

Respond with valid JSON only. No markdown fences."""

    topics_hint = ""
    if topic_ids:
        topics_hint = f"\nKnown topics in the learner's graph: {', '.join(topic_ids[:30])}"

    user = f"""Analyze this text and extract the key claims, arguments, and assumptions:

---
{article_text[:6000]}
---
{topics_hint}

For each claim, generate a targeted challenge exercise. The challenge should:
- Force the author to defend or justify the claim
- Probe assumptions the author might not have examined
- Connect to the broader field

Return JSON:
{{
  "claims": [
    {{
      "claim": "The specific claim or argument made",
      "type": "empirical|theoretical|methodological|assumption",
      "related_topics": ["topic_id_1", "topic_id_2"],
      "challenge_prompt": "A specific question that challenges this claim. E.g., 'You argue X. But what about Y? How would you respond to someone who says Z?'"
    }}
  ]
}}

Extract 3-6 claims, prioritizing the most important and challengeable ones."""

    return system, user


def parse_claims_response(response: str) -> List[ArticleClaim]:
    """Parse LLM response into ArticleClaim objects."""
    text = response.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(l for l in lines if not l.strip().startswith("```"))

    data = json.loads(text)
    claims = []
    for c in data.get("claims", []):
        claims.append(ArticleClaim(
            claim=c.get("claim", ""),
            claim_type=c.get("type", "theoretical"),
            related_topics=c.get("related_topics", []),
            challenge_prompt=c.get("challenge_prompt", ""),
        ))
    return claims


def read_article(file_path: str) -> str:
    """Read article text from file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    text = path.read_text(encoding="utf-8")

    # Strip YAML frontmatter if present
    if text.startswith("---"):
        lines = text.split("\n")
        for i, line in enumerate(lines[1:], 1):
            if line.strip() == "---":
                text = "\n".join(lines[i + 1:])
                break

    return text.strip()
