"""mental-gym suggest — context-aware training suggestions.

Called automatically by hooks or manually. Checks what changed recently
in the knowledge base, research projects, and training history, then
prints a targeted suggestion.
"""

import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

from mental_gym.config import load_config
from mental_gym.db.schema import open_db
from mental_gym.db.store import Store
from mental_gym.engine.kb_sync import detect_changes
from mental_gym.ui import Color, bold, colored, dim, print_info


def run_suggest(args):
    """Generate a context-aware training suggestion."""
    try:
        config = load_config(args.config)
    except FileNotFoundError:
        return  # Silently exit if not initialized

    try:
        conn = open_db(config.db_path)
    except FileNotFoundError:
        return

    store = Store(conn)
    suggestions = []

    # 1. Check if a specific file was changed (from hook)
    changed_file = getattr(args, "changed_file", None)
    if changed_file:
        suggestion = _suggest_for_changed_file(changed_file, store, config)
        if suggestion:
            suggestions.append(suggestion)

    # 2. Check for new/changed wiki pages
    if config.knowledge_base:
        new_files, modified_files, _ = detect_changes(store, config.knowledge_base)
        if new_files:
            new_titles = _extract_titles(config.knowledge_base, new_files[:5])
            suggestions.append({
                "type": "new_knowledge",
                "priority": 3,
                "message": _format_new_knowledge(new_titles, len(new_files)),
                "command": "mental-gym sync && mental-gym train",
            })
        if modified_files:
            mod_titles = _extract_titles(config.knowledge_base, modified_files[:3])
            suggestions.append({
                "type": "updated_knowledge",
                "priority": 2,
                "message": _format_updated_knowledge(mod_titles, len(modified_files)),
                "command": "mental-gym sync",
            })

    # 3. Check for topics due for review
    due_topics = store.get_topics_due_for_review()
    if due_topics:
        suggestions.append({
            "type": "spaced_review",
            "priority": 2 if len(due_topics) <= 3 else 3,
            "message": _format_review_due(due_topics),
            "command": "mental-gym warmup",
        })

    # 4. Check training staleness
    recent = store.get_recent_sessions(limit=1)
    if recent:
        last = datetime.fromisoformat(recent[0].started_at)
        days_ago = (datetime.utcnow() - last).days
        if days_ago >= 3:
            suggestions.append({
                "type": "staleness",
                "priority": 1,
                "message": f"It's been {days_ago} days since your last training session.",
                "command": "mental-gym train",
            })
    elif store.topic_count() > 0:
        suggestions.append({
            "type": "first_session",
            "priority": 3,
            "message": "You have topics loaded but haven't trained yet.",
            "command": "mental-gym train",
        })

    # 5. Scan for draft files in research projects
    if not changed_file:
        draft_suggestion = _check_for_drafts(store, config)
        if draft_suggestion:
            suggestions.append(draft_suggestion)

    conn.close()

    if not suggestions:
        return  # Nothing to suggest

    # Pick the highest priority suggestion
    suggestions.sort(key=lambda s: s["priority"], reverse=True)
    best = suggestions[0]

    # Format output
    print()
    print(colored("  ━━ Mental Gym ━━", Color.CYAN))
    print(f"  {best['message']}")
    print(f"  {dim('Try:')} {colored(best['command'], Color.WHITE)}")
    print()


def _suggest_for_changed_file(file_path: str, store: Store, config) -> Optional[dict]:
    """Generate a suggestion specific to a changed file, with mastery context."""
    path = Path(file_path)

    # Detect file type and generate appropriate suggestion
    is_wiki = "wiki/" in str(path)
    is_paper = "paper" in str(path).lower() or "draft" in str(path).lower()
    is_doc = path.suffix in (".md", ".tex") and ("docs/" in str(path) or is_paper)

    if not (is_wiki or is_paper or is_doc):
        return None

    # Extract topic name from file
    file_name = path.stem.replace("_", " ").replace("-", " ").title()

    # Try to find matching topic in the graph and get mastery
    mastery_info = ""
    matching_topic = None
    all_topics = store.get_all_topics()
    file_slug = path.stem.lower().replace("-", "_")
    for t in all_topics:
        if file_slug in t.id or t.id in file_slug:
            matching_topic = t
            break
        # Fuzzy: check if file name words appear in topic name
        file_words = set(file_slug.split("_"))
        topic_words = set(t.id.split("_"))
        if len(file_words & topic_words) >= 2:
            matching_topic = t
            break

    if matching_topic:
        pct = f"{matching_topic.mastery:.0%}"
        if matching_topic.mastery < 0.3:
            mastery_info = f" Your mastery of {bold(matching_topic.name)} is {colored(pct, Color.RED)}."
        elif matching_topic.mastery < 0.7:
            mastery_info = f" Your mastery of {bold(matching_topic.name)} is {colored(pct, Color.YELLOW)}."

    if is_wiki:
        msg = f"You just updated {bold(file_name)} in the wiki.{mastery_info} Test your understanding?"
        if matching_topic:
            cmd = f"mental-gym train --focus \"{matching_topic.id}\""
        else:
            cmd = f"mental-gym review {file_path}"
        return {"type": "wiki_edit", "priority": 4, "message": msg, "command": cmd}

    if is_paper or is_doc:
        msg = f"You're working on {bold(file_name)}.{mastery_info} Stress-test your arguments?"
        return {
            "type": "draft_edit", "priority": 4,
            "message": msg,
            "command": f"mental-gym review {file_path}",
        }

    return None


def _check_for_drafts(store: Store, config) -> Optional[dict]:
    """Check for recently modified draft files across research projects."""
    repo_root = Path(config.config_dir).parent
    recent_drafts = []

    # Scan for paper drafts across project directories
    for pattern in ["*/papers/*.md", "*/papers/*.tex", "*/docs/*draft*"]:
        for f in repo_root.glob(pattern):
            try:
                mtime = datetime.utcfromtimestamp(f.stat().st_mtime)
                if (datetime.utcnow() - mtime).days <= 2:
                    recent_drafts.append(f)
            except OSError:
                continue

    if recent_drafts:
        draft = recent_drafts[0]
        name = draft.stem.replace("_", " ").replace("-", " ").title()
        return {
            "type": "recent_draft",
            "priority": 1,
            "message": f"Recent draft: {bold(name)}. Review your claims before they go stale?",
            "command": f"mental-gym review {draft}",
        }
    return None


# --- Formatting helpers ---

def _extract_titles(kb_path: str, file_paths: List[str]) -> List[str]:
    """Extract titles from KB files."""
    titles = []
    for rel in file_paths:
        full = Path(kb_path) / rel
        if not full.exists():
            titles.append(Path(rel).stem.replace("_", " ").replace("-", " ").title())
            continue
        try:
            text = full.read_text(encoding="utf-8")
            for line in text.split("\n"):
                if line.startswith("# "):
                    titles.append(line[2:].strip())
                    break
            else:
                titles.append(Path(rel).stem.replace("_", " ").replace("-", " ").title())
        except Exception:
            titles.append(Path(rel).stem.replace("_", " ").title())
    return titles


def _format_new_knowledge(titles: List[str], total: int) -> str:
    if total == 1:
        return f"New in your knowledge base: {bold(titles[0])}. Test your understanding?"
    shown = ", ".join(bold(t) for t in titles[:3])
    extra = f" (+{total - 3} more)" if total > 3 else ""
    return f"{total} new pages in your knowledge base: {shown}{extra}. Ready to practice?"


def _format_updated_knowledge(titles: List[str], total: int) -> str:
    shown = ", ".join(bold(t) for t in titles[:3])
    return f"{total} updated pages: {shown}. Your understanding may need refreshing."


def _format_review_due(topics) -> str:
    names = [t.name for t in topics[:3]]
    shown = ", ".join(bold(n) for n in names)
    if len(topics) > 3:
        return f"{len(topics)} topics due for review, including {shown}."
    return f"Due for review: {shown}."
