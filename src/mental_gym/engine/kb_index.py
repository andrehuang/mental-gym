"""Knowledge base vector index — chunk, embed, store, retrieve.

Uses fastembed for local embeddings and sqlite-vec for vector storage.
"""

import hashlib
import json
import re
import sqlite3
import struct
from pathlib import Path
from typing import List, Optional, Tuple

# Lazy imports for optional dependencies
_embedder = None


def _get_embedder():
    """Lazy-load the embedding model."""
    global _embedder
    if _embedder is None:
        from fastembed import TextEmbedding
        _embedder = TextEmbedding("BAAI/bge-small-en-v1.5")
    return _embedder


def _embed_texts(texts: List[str]) -> List[List[float]]:
    """Embed a list of texts using the local model."""
    model = _get_embedder()
    return [emb.tolist() for emb in model.embed(texts)]


def _serialize_vec(vec: List[float]) -> bytes:
    """Serialize a float vector to bytes for sqlite-vec."""
    return struct.pack(f"{len(vec)}f", *vec)


def _ensure_vec_table(conn: sqlite3.Connection):
    """Create the virtual table for vector search if it doesn't exist."""
    import sqlite_vec
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)

    # Check if table exists
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='kb_chunks'"
    )
    if cur.fetchone():
        return

    # Create metadata table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS kb_chunks_meta (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT NOT NULL,
            chunk_index INTEGER NOT NULL,
            chunk_text TEXT NOT NULL,
            file_hash TEXT NOT NULL,
            topic_id TEXT,
            UNIQUE(file_path, chunk_index)
        )
    """)

    # Create vector table (384 dimensions for bge-small-en-v1.5)
    conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS kb_chunks
        USING vec0(embedding float[384])
    """)

    conn.commit()


def chunk_markdown(text: str, max_tokens: int = 400) -> List[str]:
    """Split markdown text into chunks, respecting paragraph boundaries.

    Aims for ~400 tokens per chunk (~300 words).
    """
    # Strip YAML frontmatter
    if text.startswith("---"):
        lines = text.split("\n")
        for i, line in enumerate(lines[1:], 1):
            if line.strip() == "---":
                text = "\n".join(lines[i + 1:])
                break

    # Split on double newlines (paragraph boundaries)
    paragraphs = re.split(r"\n\s*\n", text.strip())
    paragraphs = [p.strip() for p in paragraphs if p.strip()]

    chunks = []
    current = []
    current_len = 0

    for para in paragraphs:
        para_words = len(para.split())
        if current_len + para_words > max_tokens and current:
            chunks.append("\n\n".join(current))
            current = [para]
            current_len = para_words
        else:
            current.append(para)
            current_len += para_words

    if current:
        chunks.append("\n\n".join(current))

    return chunks


def build_index(conn: sqlite3.Connection, kb_path: str,
                progress_callback=None) -> Tuple[int, int]:
    """Build or rebuild the full KB vector index.

    Returns (files_indexed, chunks_created).
    """
    _ensure_vec_table(conn)

    kb = Path(kb_path)
    if not kb.is_dir():
        return 0, 0

    # Collect all markdown files
    md_files = sorted(f for f in kb.rglob("*.md")
                      if f.name not in ("index.md", "log.md", "wiki.schema.md"))

    files_indexed = 0
    chunks_created = 0

    for md_file in md_files:
        rel = str(md_file.relative_to(kb))
        file_hash = hashlib.md5(md_file.read_bytes()).hexdigest()

        # Check if already indexed with same hash
        existing = conn.execute(
            "SELECT file_hash FROM kb_chunks_meta WHERE file_path = ? LIMIT 1",
            (rel,)
        ).fetchone()
        if existing and existing[0] == file_hash:
            continue  # Already up to date

        # Remove old chunks for this file
        old_ids = [
            row[0] for row in conn.execute(
                "SELECT id FROM kb_chunks_meta WHERE file_path = ?", (rel,)
            ).fetchall()
        ]
        if old_ids:
            placeholders = ",".join("?" * len(old_ids))
            conn.execute(f"DELETE FROM kb_chunks WHERE rowid IN ({placeholders})", old_ids)
            conn.execute(f"DELETE FROM kb_chunks_meta WHERE id IN ({placeholders})", old_ids)

        # Read and chunk
        try:
            text = md_file.read_text(encoding="utf-8")
        except Exception:
            continue

        chunks = chunk_markdown(text)
        if not chunks:
            continue

        # Derive topic_id from filename
        topic_id = md_file.stem.replace(" ", "_").replace("-", "_").lower()

        # Embed all chunks
        embeddings = _embed_texts(chunks)

        # Insert chunks
        for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
            cur = conn.execute(
                """INSERT INTO kb_chunks_meta (file_path, chunk_index, chunk_text, file_hash, topic_id)
                   VALUES (?, ?, ?, ?, ?)""",
                (rel, i, chunk, file_hash, topic_id),
            )
            chunk_id = cur.lastrowid
            conn.execute(
                "INSERT INTO kb_chunks (rowid, embedding) VALUES (?, ?)",
                (chunk_id, _serialize_vec(emb)),
            )

        files_indexed += 1
        chunks_created += len(chunks)

        if progress_callback:
            progress_callback(rel, len(chunks))

    conn.commit()
    return files_indexed, chunks_created


def retrieve_chunks(conn: sqlite3.Connection, query: str,
                    topic_id: Optional[str] = None,
                    limit: int = 5) -> List[dict]:
    """Retrieve the most relevant KB chunks for a query.

    Returns list of {"text": ..., "file_path": ..., "score": ...}.
    """
    try:
        _ensure_vec_table(conn)
    except Exception:
        return []  # sqlite-vec not available

    # Embed the query
    embeddings = _embed_texts([query])
    query_vec = _serialize_vec(embeddings[0])

    # Vector similarity search — sqlite-vec requires k=? in the WHERE clause
    # Fetch more than needed so we can re-rank by topic affinity
    fetch_limit = limit * 3 if topic_id else limit
    rows = conn.execute("""
        SELECT m.chunk_text, m.file_path, v.distance, m.topic_id
        FROM kb_chunks v
        JOIN kb_chunks_meta m ON m.id = v.rowid
        WHERE v.embedding MATCH ? AND k = ?
        ORDER BY v.distance
    """, (query_vec, fetch_limit)).fetchall()

    if topic_id:
        # Re-rank: prefer chunks from the matching topic
        rows = sorted(rows, key=lambda r: (0 if r[3] == topic_id else 1, r[2]))
    rows = rows[:limit]

    return [
        {"text": row[0], "file_path": row[1], "score": row[2]}
        for row in rows
    ]


def get_index_stats(conn: sqlite3.Connection) -> dict:
    """Get stats about the current index."""
    try:
        _ensure_vec_table(conn)
        chunk_count = conn.execute("SELECT COUNT(*) FROM kb_chunks_meta").fetchone()[0]
        file_count = conn.execute(
            "SELECT COUNT(DISTINCT file_path) FROM kb_chunks_meta"
        ).fetchone()[0]
        return {"chunks": chunk_count, "files": file_count}
    except Exception:
        return {"chunks": 0, "files": 0}
