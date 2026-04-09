"""SQLite schema definition and migration."""

import sqlite3
from pathlib import Path

SCHEMA_VERSION = 1

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS topics (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    mastery REAL DEFAULT 0.0,
    difficulty_level INTEGER DEFAULT 1,
    times_tested INTEGER DEFAULT 0,
    last_tested TEXT,
    next_review TEXT,
    sm2_interval REAL DEFAULT 1.0,
    sm2_easiness REAL DEFAULT 2.5,
    sm2_repetitions INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    source TEXT,
    kb_file_path TEXT,
    kb_file_hash TEXT
);

CREATE TABLE IF NOT EXISTS topic_connections (
    topic_a TEXT NOT NULL REFERENCES topics(id),
    topic_b TEXT NOT NULL REFERENCES topics(id),
    relationship TEXT,
    PRIMARY KEY (topic_a, topic_b)
);

CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL,
    ended_at TEXT,
    duration_seconds INTEGER,
    focus_topic TEXT,
    exercise_count INTEGER DEFAULT 0,
    avg_score REAL
);

CREATE TABLE IF NOT EXISTS exercises (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER REFERENCES sessions(id),
    exercise_type TEXT NOT NULL,
    topic_id TEXT REFERENCES topics(id),
    secondary_topic_id TEXT,
    difficulty_level INTEGER NOT NULL,
    phase TEXT NOT NULL,
    prompt TEXT NOT NULL,
    user_response TEXT,
    score_accuracy REAL,
    score_completeness REAL,
    score_depth REAL,
    overall_score REAL,
    feedback TEXT,
    key_points TEXT,
    created_at TEXT NOT NULL,
    duration_seconds INTEGER
);

CREATE TABLE IF NOT EXISTS mastery_notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exercise_id INTEGER REFERENCES exercises(id),
    topic_id TEXT REFERENCES topics(id),
    note_type TEXT NOT NULL,
    concept TEXT NOT NULL,
    detail TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS kb_sync_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    synced_at TEXT NOT NULL,
    files_scanned INTEGER,
    new_topics_added INTEGER,
    topics_updated INTEGER,
    new_files TEXT,
    modified_files TEXT
);
"""


def init_db(db_path: str) -> sqlite3.Connection:
    """Create database and initialize schema."""
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(SCHEMA_SQL)

    # Set schema version if not set
    cur = conn.execute("SELECT COUNT(*) FROM schema_version")
    if cur.fetchone()[0] == 0:
        conn.execute("INSERT INTO schema_version VALUES (?)", (SCHEMA_VERSION,))

    conn.commit()
    return conn


def open_db(db_path: str) -> sqlite3.Connection:
    """Open existing database."""
    if not Path(db_path).exists():
        raise FileNotFoundError(
            f"Database not found: {db_path}\n"
            "Run 'mental-gym init' first."
        )
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn
