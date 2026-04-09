"""Prompt templates for topic graph generation and exercise generation."""


def topic_graph_prompt(domain: str, kb_summary: str) -> tuple[str, str]:
    """Return (system_prompt, user_prompt) for generating initial topic graph.

    Returns a tuple of (system_prompt, user_prompt).
    """
    system = f"""You are an expert in {domain} helping to build a study curriculum.
Your task is to generate a topic graph — a set of core concepts/topics that someone
needs to master to become a domain expert.

Respond with valid JSON only. No markdown, no explanation outside the JSON."""

    user = f"""Generate a topic graph for the domain: {domain}

{f"The learner has the following materials in their knowledge base:{chr(10)}{kb_summary}" if kb_summary else "No knowledge base provided — generate from your general knowledge of the field."}

Generate 30-50 core topics. For each topic, provide:
- id: a short snake_case slug (e.g., "emergence_vs_leakage")
- name: human-readable name
- description: 1-2 sentence description of what this concept covers
- connections: list of other topic ids this topic is related to

The topics should cover:
- Foundational concepts and theories
- Key methodological approaches
- Important debates and open questions
- Influential papers and frameworks
- Practical skills and techniques

Return JSON in this exact format:
{{
  "topics": [
    {{
      "id": "topic_slug",
      "name": "Topic Name",
      "description": "What this topic covers.",
      "connections": ["other_topic_id_1", "other_topic_id_2"]
    }}
  ]
}}"""

    return system, user


def scan_knowledge_base(kb_path: str) -> str:
    """Scan knowledge base directory, return summary string for LLM."""
    import os
    from pathlib import Path

    kb = Path(kb_path)
    if not kb.is_dir():
        return ""

    entries = []
    for md_file in sorted(kb.rglob("*.md")):
        rel = md_file.relative_to(kb)
        # Skip index files and schema files
        if rel.name in ("index.md", "log.md"):
            continue

        try:
            text = md_file.read_text(encoding="utf-8")
        except Exception:
            continue

        # Extract title from first heading or frontmatter
        title = None
        description = ""
        lines = text.split("\n")

        # Check YAML frontmatter
        if lines and lines[0].strip() == "---":
            for i, line in enumerate(lines[1:], 1):
                if line.strip() == "---":
                    # Parse frontmatter
                    for fm_line in lines[1:i]:
                        if fm_line.startswith("title:"):
                            title = fm_line.split(":", 1)[1].strip().strip('"').strip("'")
                        elif fm_line.startswith("summary:"):
                            description = fm_line.split(":", 1)[1].strip().strip('"').strip("'")
                    break

        # Fall back to first heading
        if not title:
            for line in lines:
                if line.startswith("# "):
                    title = line[2:].strip()
                    break

        if not title:
            title = rel.stem.replace("_", " ").replace("-", " ").title()

        # Get first paragraph after title for description
        if not description:
            in_content = False
            for line in lines:
                if line.startswith("# "):
                    in_content = True
                    continue
                if in_content and line.strip() and not line.startswith("---"):
                    description = line.strip()[:200]
                    break

        entries.append(f"- {rel}: {title}" + (f" — {description}" if description else ""))

    return "\n".join(entries[:60])  # Cap at 60 entries to stay within context
