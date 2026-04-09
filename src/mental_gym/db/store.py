"""Data access layer — all DB reads and writes."""

import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class Topic:
    id: str
    name: str
    description: str = ""
    mastery: float = 0.0
    difficulty_level: int = 1
    times_tested: int = 0
    last_tested: Optional[str] = None
    next_review: Optional[str] = None
    sm2_interval: float = 1.0
    sm2_easiness: float = 2.5
    sm2_repetitions: int = 0
    created_at: str = ""
    source: str = "generated"
    kb_file_path: Optional[str] = None
    kb_file_hash: Optional[str] = None


@dataclass
class TopicConnection:
    topic_a: str
    topic_b: str
    relationship: str = "related"


@dataclass
class Exercise:
    id: Optional[int] = None
    session_id: Optional[int] = None
    exercise_type: str = ""
    topic_id: str = ""
    secondary_topic_id: Optional[str] = None
    difficulty_level: int = 1
    phase: str = "main"
    prompt: str = ""
    user_response: Optional[str] = None
    score_accuracy: Optional[float] = None
    score_completeness: Optional[float] = None
    score_depth: Optional[float] = None
    overall_score: Optional[float] = None
    feedback: Optional[str] = None
    key_points: Optional[str] = None  # JSON string
    created_at: str = ""
    duration_seconds: Optional[int] = None


@dataclass
class MasteryNote:
    id: Optional[int] = None
    exercise_id: Optional[int] = None
    topic_id: str = ""
    note_type: str = ""  # "demonstrated" | "missed" | "misconception" | "partial"
    concept: str = ""
    detail: Optional[str] = None
    created_at: str = ""


@dataclass
class Session:
    id: Optional[int] = None
    started_at: str = ""
    ended_at: Optional[str] = None
    duration_seconds: Optional[int] = None
    focus_topic: Optional[str] = None
    exercise_count: int = 0
    avg_score: Optional[float] = None


class Store:
    """Data access layer for Mental Gym database."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    # --- Topics ---

    def insert_topic(self, topic: Topic):
        now = datetime.utcnow().isoformat()
        self.conn.execute(
            """INSERT OR IGNORE INTO topics
               (id, name, description, mastery, difficulty_level,
                created_at, source, kb_file_path, kb_file_hash)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (topic.id, topic.name, topic.description, topic.mastery,
             topic.difficulty_level, topic.created_at or now,
             topic.source, topic.kb_file_path, topic.kb_file_hash),
        )
        self.conn.commit()

    def insert_topics_batch(self, topics: List[Topic]):
        now = datetime.utcnow().isoformat()
        rows = [
            (t.id, t.name, t.description, t.mastery, t.difficulty_level,
             t.created_at or now, t.source, t.kb_file_path, t.kb_file_hash)
            for t in topics
        ]
        self.conn.executemany(
            """INSERT OR IGNORE INTO topics
               (id, name, description, mastery, difficulty_level,
                created_at, source, kb_file_path, kb_file_hash)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            rows,
        )
        self.conn.commit()

    def get_topic(self, topic_id: str) -> Optional[Topic]:
        row = self.conn.execute(
            "SELECT * FROM topics WHERE id = ?", (topic_id,)
        ).fetchone()
        if not row:
            return None
        return self._row_to_topic(row)

    def get_all_topics(self) -> List[Topic]:
        rows = self.conn.execute(
            "SELECT * FROM topics ORDER BY name"
        ).fetchall()
        return [self._row_to_topic(r) for r in rows]

    def get_topics_due_for_review(self, now: Optional[str] = None) -> List[Topic]:
        now = now or datetime.utcnow().isoformat()
        rows = self.conn.execute(
            """SELECT * FROM topics
               WHERE next_review IS NOT NULL AND next_review <= ?
               ORDER BY next_review ASC""",
            (now,),
        ).fetchall()
        return [self._row_to_topic(r) for r in rows]

    def get_weakest_topics(self, limit: int = 5) -> List[Topic]:
        rows = self.conn.execute(
            """SELECT * FROM topics
               ORDER BY mastery ASC, times_tested ASC
               LIMIT ?""",
            (limit,),
        ).fetchall()
        return [self._row_to_topic(r) for r in rows]

    def get_untested_topics(self, limit: int = 5) -> List[Topic]:
        rows = self.conn.execute(
            """SELECT * FROM topics
               WHERE times_tested = 0
               ORDER BY created_at ASC
               LIMIT ?""",
            (limit,),
        ).fetchall()
        return [self._row_to_topic(r) for r in rows]

    def update_topic_mastery(self, topic_id: str, mastery: float,
                             difficulty_level: int, sm2_interval: float,
                             sm2_easiness: float, sm2_repetitions: int,
                             next_review: str):
        now = datetime.utcnow().isoformat()
        self.conn.execute(
            """UPDATE topics SET
               mastery = ?, difficulty_level = ?, times_tested = times_tested + 1,
               last_tested = ?, next_review = ?,
               sm2_interval = ?, sm2_easiness = ?, sm2_repetitions = ?
               WHERE id = ?""",
            (mastery, difficulty_level, now, next_review,
             sm2_interval, sm2_easiness, sm2_repetitions, topic_id),
        )
        self.conn.commit()

    def topic_count(self) -> int:
        row = self.conn.execute("SELECT COUNT(*) FROM topics").fetchone()
        return row[0]

    def _row_to_topic(self, row) -> Topic:
        return Topic(
            id=row["id"], name=row["name"], description=row["description"],
            mastery=row["mastery"], difficulty_level=row["difficulty_level"],
            times_tested=row["times_tested"], last_tested=row["last_tested"],
            next_review=row["next_review"], sm2_interval=row["sm2_interval"],
            sm2_easiness=row["sm2_easiness"], sm2_repetitions=row["sm2_repetitions"],
            created_at=row["created_at"], source=row["source"],
            kb_file_path=row["kb_file_path"], kb_file_hash=row["kb_file_hash"],
        )

    # --- Topic connections ---

    def insert_connection(self, conn_obj: TopicConnection):
        self.conn.execute(
            """INSERT OR IGNORE INTO topic_connections
               (topic_a, topic_b, relationship) VALUES (?, ?, ?)""",
            (conn_obj.topic_a, conn_obj.topic_b, conn_obj.relationship),
        )
        self.conn.commit()

    def insert_connections_batch(self, connections: List[TopicConnection]):
        rows = [(c.topic_a, c.topic_b, c.relationship) for c in connections]
        self.conn.executemany(
            """INSERT OR IGNORE INTO topic_connections
               (topic_a, topic_b, relationship) VALUES (?, ?, ?)""",
            rows,
        )
        self.conn.commit()

    def get_connected_topics(self, topic_id: str) -> List[str]:
        rows = self.conn.execute(
            """SELECT topic_b FROM topic_connections WHERE topic_a = ?
               UNION
               SELECT topic_a FROM topic_connections WHERE topic_b = ?""",
            (topic_id, topic_id),
        ).fetchall()
        return [r[0] for r in rows]

    # --- Sessions ---

    def create_session(self, focus_topic: Optional[str] = None) -> int:
        now = datetime.utcnow().isoformat()
        cur = self.conn.execute(
            """INSERT INTO sessions (started_at, focus_topic)
               VALUES (?, ?)""",
            (now, focus_topic),
        )
        self.conn.commit()
        return cur.lastrowid

    def end_session(self, session_id: int, exercise_count: int, avg_score: float):
        now = datetime.utcnow().isoformat()
        started = self.conn.execute(
            "SELECT started_at FROM sessions WHERE id = ?", (session_id,)
        ).fetchone()
        duration = None
        if started:
            start_dt = datetime.fromisoformat(started["started_at"])
            duration = int((datetime.utcnow() - start_dt).total_seconds())
        self.conn.execute(
            """UPDATE sessions SET
               ended_at = ?, duration_seconds = ?,
               exercise_count = ?, avg_score = ?
               WHERE id = ?""",
            (now, duration, exercise_count, avg_score, session_id),
        )
        self.conn.commit()

    def get_session_count(self) -> int:
        row = self.conn.execute("SELECT COUNT(*) FROM sessions").fetchone()
        return row[0]

    def get_recent_sessions(self, limit: int = 5) -> List[Session]:
        rows = self.conn.execute(
            "SELECT * FROM sessions ORDER BY started_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [
            Session(
                id=r["id"], started_at=r["started_at"], ended_at=r["ended_at"],
                duration_seconds=r["duration_seconds"], focus_topic=r["focus_topic"],
                exercise_count=r["exercise_count"], avg_score=r["avg_score"],
            )
            for r in rows
        ]

    # --- Exercises ---

    def insert_exercise(self, exercise: Exercise) -> int:
        now = datetime.utcnow().isoformat()
        cur = self.conn.execute(
            """INSERT INTO exercises
               (session_id, exercise_type, topic_id, secondary_topic_id,
                difficulty_level, phase, prompt, user_response,
                score_accuracy, score_completeness, score_depth, overall_score,
                feedback, key_points, created_at, duration_seconds)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (exercise.session_id, exercise.exercise_type, exercise.topic_id,
             exercise.secondary_topic_id, exercise.difficulty_level, exercise.phase,
             exercise.prompt, exercise.user_response,
             exercise.score_accuracy, exercise.score_completeness,
             exercise.score_depth, exercise.overall_score,
             exercise.feedback, exercise.key_points,
             exercise.created_at or now, exercise.duration_seconds),
        )
        self.conn.commit()
        return cur.lastrowid

    # --- Mastery notes ---

    def insert_mastery_notes(self, notes: List[MasteryNote]):
        now = datetime.utcnow().isoformat()
        rows = [
            (n.exercise_id, n.topic_id, n.note_type, n.concept,
             n.detail, n.created_at or now)
            for n in notes
        ]
        self.conn.executemany(
            """INSERT INTO mastery_notes
               (exercise_id, topic_id, note_type, concept, detail, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            rows,
        )
        self.conn.commit()

    def get_mastery_notes_for_topic(self, topic_id: str,
                                     limit: int = 10) -> List[MasteryNote]:
        rows = self.conn.execute(
            """SELECT * FROM mastery_notes
               WHERE topic_id = ?
               ORDER BY created_at DESC LIMIT ?""",
            (topic_id, limit),
        ).fetchall()
        return [
            MasteryNote(
                id=r["id"], exercise_id=r["exercise_id"], topic_id=r["topic_id"],
                note_type=r["note_type"], concept=r["concept"],
                detail=r["detail"], created_at=r["created_at"],
            )
            for r in rows
        ]
