"""Knowledge base sync — detect changes, propose new topics."""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from mental_gym.db.store import Store, Topic


def file_hash(path: Path) -> str:
    """Compute MD5 hash of a file."""
    return hashlib.md5(path.read_bytes()).hexdigest()


def scan_kb_files(kb_path: str) -> dict[str, str]:
    """Scan KB directory, return {relative_path: hash} for all .md files."""
    kb = Path(kb_path)
    if not kb.is_dir():
        return {}
    result = {}
    for md_file in sorted(kb.rglob("*.md")):
        if md_file.name in ("index.md", "log.md"):
            continue
        rel = str(md_file.relative_to(kb))
        result[rel] = file_hash(md_file)
    return result


def detect_changes(store: Store, kb_path: str) -> Tuple[List[str], List[str], List[str]]:
    """Compare current KB state against stored hashes.

    Returns (new_files, modified_files, deleted_files).
    """
    current_files = scan_kb_files(kb_path)

    # Get stored file hashes from topics
    topics = store.get_all_topics()
    stored = {}
    for t in topics:
        if t.kb_file_path and t.kb_file_hash:
            stored[t.kb_file_path] = t.kb_file_hash

    # Also check the sync log for the full set of known files
    new_files = [f for f in current_files if f not in stored]
    modified_files = [
        f for f in current_files
        if f in stored and current_files[f] != stored[f]
    ]
    deleted_files = [f for f in stored if f not in current_files]

    return new_files, modified_files, deleted_files


def extract_topic_from_file(kb_path: str, rel_path: str) -> Optional[dict]:
    """Extract topic info from a KB markdown file.

    Returns dict with id, name, description, or None if parsing fails.
    """
    full_path = Path(kb_path) / rel_path
    if not full_path.exists():
        return None

    try:
        text = full_path.read_text(encoding="utf-8")
    except Exception:
        return None

    lines = text.split("\n")
    title = None
    description = ""

    # Parse YAML frontmatter
    if lines and lines[0].strip() == "---":
        for i, line in enumerate(lines[1:], 1):
            if line.strip() == "---":
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
        title = Path(rel_path).stem.replace("_", " ").replace("-", " ").title()

    # Get first content paragraph
    if not description:
        in_content = False
        for line in lines:
            if line.startswith("# "):
                in_content = True
                continue
            if in_content and line.strip() and not line.startswith("---") and not line.startswith("```"):
                description = line.strip()[:200]
                break

    # Generate ID from filename
    topic_id = Path(rel_path).stem.replace(" ", "_").replace("-", "_").lower()

    return {
        "id": topic_id,
        "name": title,
        "description": description,
        "rel_path": rel_path,
        "hash": file_hash(Path(kb_path) / rel_path),
    }


def apply_sync(store: Store, kb_path: str,
               new_files: List[str], modified_files: List[str]):
    """Apply sync changes: add new topics, update modified ones."""
    added = 0
    updated = 0
    now = datetime.utcnow().isoformat()

    for f in new_files:
        info = extract_topic_from_file(kb_path, f)
        if info:
            topic = Topic(
                id=info["id"],
                name=info["name"],
                description=info["description"],
                source="knowledge_base",
                kb_file_path=info["rel_path"],
                kb_file_hash=info["hash"],
                created_at=now,
            )
            store.insert_topic(topic)
            added += 1

    for f in modified_files:
        info = extract_topic_from_file(kb_path, f)
        if info:
            # Update existing topic's name, description, and hash
            existing = store.get_topic(info["id"])
            if existing:
                store.conn.execute(
                    """UPDATE topics SET name = ?, description = ?, kb_file_hash = ?
                       WHERE id = ?""",
                    (info["name"], info["description"], info["hash"], info["id"]),
                )
                store.conn.commit()
                updated += 1

    # Log the sync
    store.conn.execute(
        """INSERT INTO kb_sync_log
           (synced_at, files_scanned, new_topics_added, topics_updated,
            new_files, modified_files)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (now, len(new_files) + len(modified_files), added, updated,
         json.dumps(new_files), json.dumps(modified_files)),
    )
    store.conn.commit()

    return added, updated


def retire_deleted(store: Store, deleted_files: List[str]) -> int:
    """Retire topics whose KB source files have been deleted.

    Sets kb_file_path and kb_file_hash to NULL so the topic is no longer
    tied to a file, and marks it as source='retired'. The topic stays in the
    DB (preserving mastery data) but won't be selected for new exercises.
    """
    retired = 0
    for f in deleted_files:
        # Find topics linked to this file
        rows = store.conn.execute(
            "SELECT id FROM topics WHERE kb_file_path = ?", (f,)
        ).fetchall()
        for row in rows:
            store.conn.execute(
                """UPDATE topics SET kb_file_path = NULL, kb_file_hash = NULL,
                   source = 'retired' WHERE id = ?""",
                (row["id"],),
            )
            retired += 1
    if retired:
        store.conn.commit()
    return retired


def quick_sync_check(store: Store, kb_path: str) -> bool:
    """Lightweight check: has the KB directory changed since last sync?

    Uses directory mtime as a quick heuristic.
    """
    if not kb_path:
        return False

    kb = Path(kb_path)
    if not kb.is_dir():
        return False

    # Get last sync time
    row = store.conn.execute(
        "SELECT synced_at FROM kb_sync_log ORDER BY synced_at DESC LIMIT 1"
    ).fetchone()

    if not row:
        # Never synced — changes likely exist
        return True

    last_sync = datetime.fromisoformat(row["synced_at"])

    # Check if any file is newer than last sync
    for md_file in kb.rglob("*.md"):
        mtime = datetime.utcfromtimestamp(md_file.stat().st_mtime)
        if mtime > last_sync:
            return True

    return False
