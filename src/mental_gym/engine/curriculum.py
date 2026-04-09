"""Adaptive curriculum — topic selection and session planning."""

import random
from dataclasses import dataclass
from typing import List, Optional

from mental_gym.db.store import Store, Topic
from mental_gym.engine.memory import mastery_to_difficulty


@dataclass
class ExercisePlan:
    """A planned exercise within a session."""
    topic_id: str
    topic_name: str
    topic_description: str
    exercise_type: str  # "explain", "predict", "connect", "defend"
    difficulty: int
    phase: str  # "warmup", "main", "cooldown"
    secondary_topic_id: Optional[str] = None
    secondary_topic_name: Optional[str] = None


def build_session_plan(store: Store,
                       focus_topic: Optional[str] = None,
                       warmup_only: bool = False) -> List[ExercisePlan]:
    """Build a session plan based on curriculum priorities.

    Priority order for topic selection:
    1. Topics due for spaced repetition review
    2. Focused topic (if specified)
    3. Weakest topics (lowest mastery)
    4. Untested topics

    Session structure:
    - Warm-up: 2 exercises on review-due topics (recall level)
    - Main: 2-3 exercises on weak/focus topics (appropriate difficulty)
    - Cool-down: 1 connect-the-dots exercise
    """
    plan = []

    # Phase 1: Warm-up — review due topics
    due_topics = store.get_topics_due_for_review()
    warmup_topics = due_topics[:2]

    for t in warmup_topics:
        plan.append(ExercisePlan(
            topic_id=t.id,
            topic_name=t.name,
            topic_description=t.description or "",
            exercise_type="explain",  # Recall-level for warm-up
            difficulty=max(1, mastery_to_difficulty(t.mastery) - 1),  # One level below current
            phase="warmup",
        ))

    if warmup_only:
        # For warmup command: add more review exercises
        for t in due_topics[2:6]:
            plan.append(ExercisePlan(
                topic_id=t.id,
                topic_name=t.name,
                topic_description=t.description or "",
                exercise_type=random.choice(["explain", "predict"]),
                difficulty=max(1, mastery_to_difficulty(t.mastery) - 1),
                phase="warmup",
            ))
        # If not enough due topics, add untested
        if len(plan) < 4:
            for t in store.get_untested_topics(limit=4 - len(plan)):
                plan.append(ExercisePlan(
                    topic_id=t.id,
                    topic_name=t.name,
                    topic_description=t.description or "",
                    exercise_type="explain",
                    difficulty=1,
                    phase="warmup",
                ))
        return plan

    # Phase 2: Main — focus or weak topics
    main_types = ["explain", "predict", "defend", "teach", "write"]
    used_topic_ids = {p.topic_id for p in plan}

    # Get candidate topics for main phase
    if focus_topic:
        # Find the focus topic
        focus = store.get_topic(focus_topic)
        if focus:
            main_candidates = [focus]
            # Add connected topics
            connected_ids = store.get_connected_topics(focus.id)
            for cid in connected_ids[:2]:
                t = store.get_topic(cid)
                if t and t.id not in used_topic_ids:
                    main_candidates.append(t)
        else:
            # Fuzzy match: search by name
            all_topics = store.get_all_topics()
            main_candidates = [
                t for t in all_topics
                if focus_topic.lower() in t.name.lower() or focus_topic.lower() in t.id
            ][:3]
    else:
        # Default: weakest topics not already in warm-up
        weak = store.get_weakest_topics(limit=10)
        main_candidates = [t for t in weak if t.id not in used_topic_ids][:3]

    # If still short, add untested topics
    if len(main_candidates) < 2:
        untested = store.get_untested_topics(limit=5)
        for t in untested:
            if t.id not in used_topic_ids and t not in main_candidates:
                main_candidates.append(t)
                if len(main_candidates) >= 3:
                    break

    for i, t in enumerate(main_candidates[:3]):
        ex_type = main_types[i % len(main_types)]
        plan.append(ExercisePlan(
            topic_id=t.id,
            topic_name=t.name,
            topic_description=t.description or "",
            exercise_type=ex_type,
            difficulty=mastery_to_difficulty(t.mastery),
            phase="main",
        ))
        used_topic_ids.add(t.id)

    # Phase 3: Cool-down — connect the dots
    all_topics = store.get_all_topics()
    cooldown_candidates = [t for t in all_topics if t.id not in used_topic_ids]

    if len(cooldown_candidates) >= 2:
        # Pick two random topics to connect
        pair = random.sample(cooldown_candidates, 2)
        plan.append(ExercisePlan(
            topic_id=pair[0].id,
            topic_name=pair[0].name,
            topic_description=pair[0].description or "",
            exercise_type="connect",
            difficulty=max(3, mastery_to_difficulty(pair[0].mastery)),
            phase="cooldown",
            secondary_topic_id=pair[1].id,
            secondary_topic_name=pair[1].name,
        ))
    elif cooldown_candidates:
        # Only one available — use it for explain
        t = cooldown_candidates[0]
        plan.append(ExercisePlan(
            topic_id=t.id,
            topic_name=t.name,
            topic_description=t.description or "",
            exercise_type="explain",
            difficulty=mastery_to_difficulty(t.mastery),
            phase="cooldown",
        ))

    return plan
