"""Session orchestration — the main training loop."""

import json
import time
from datetime import datetime
from typing import Optional

from mental_gym.config import MentalGymConfig
from mental_gym.db.store import Exercise, MasteryNote, Store
from mental_gym.engine.assessor import evaluate_response, generate_exercise
from mental_gym.engine.curriculum import ExercisePlan, build_session_plan
from mental_gym.engine.llm import LLMBackend
from mental_gym.engine.memory import sm2_update, update_mastery
from mental_gym.prompts.evaluation import get_exercise_type
from mental_gym.ui import (
    Color, bold, collect_response, collect_response_editor, colored, dim,
    print_error, print_exercise_header, print_feedback, print_header,
    print_info, print_prompt, print_separator, print_session_summary,
    print_success,
)


def run_session(config: MentalGymConfig, store: Store, llm: LLMBackend,
                focus: Optional[str] = None, warmup_only: bool = False):
    """Run a complete training session."""

    # Quick KB sync check
    if config.knowledge_base:
        from mental_gym.engine.kb_sync import quick_sync_check
        if quick_sync_check(store, config.knowledge_base):
            print_info("Knowledge base has changed since last sync. Run 'mental-gym sync' to update topics.")
            print()

    # Build session plan
    plan = build_session_plan(store, focus_topic=focus, warmup_only=warmup_only)

    if not plan:
        print_error("No topics available for training. Add topics first.")
        return

    session_num = store.get_session_count() + 1
    session_id = store.create_session(focus_topic=focus)

    session_type = "Warm-up" if warmup_only else "Training"
    print_header(f"Mental Gym — {session_type} Session #{session_num}")
    print(f"  Domain: {config.domain}")
    if focus:
        print(f"  Focus: {focus}")
    print(f"  Exercises: {len(plan)}")
    print()

    scores = []
    topic_deltas = {}  # topic_name -> (old_mastery, new_mastery)
    exercises_done = 0
    session_start = time.time()

    try:
        for i, ex_plan in enumerate(plan, 1):
            try:
                result = _run_single_exercise(
                    i, len(plan), ex_plan, config, store, llm, session_id,
                )
                if result is not None:
                    scores.append(result["overall"])
                    exercises_done += 1
                    if result.get("mastery_delta"):
                        name, old, new = result["mastery_delta"]
                        topic_deltas[name] = (old, new)
            except KeyboardInterrupt:
                print()
                print_info("Session interrupted. Saving progress...")
                break
            except Exception as e:
                print_error(f"Exercise failed: {e}")
                continue

    except KeyboardInterrupt:
        print()
        print_info("Session interrupted. Saving progress...")

    # Session summary
    duration = int(time.time() - session_start)
    avg_score = sum(scores) / len(scores) if scores else 0.0
    store.end_session(session_id, exercises_done, avg_score)

    print_session_summary(session_num, exercises_done, avg_score, duration, topic_deltas)


def _run_single_exercise(index: int, total: int, plan: ExercisePlan,
                          config: MentalGymConfig, store: Store,
                          llm: LLMBackend, session_id: int) -> Optional[dict]:
    """Run a single exercise: generate -> display -> collect -> evaluate -> record."""

    ex_type = get_exercise_type(plan.exercise_type)

    # Get mastery notes for targeted exercise generation
    mastery_notes_text = ""
    recent_notes = store.get_mastery_notes_for_topic(plan.topic_id, limit=5)
    if recent_notes:
        notes_list = [f"- {n.note_type}: {n.concept}" for n in recent_notes]
        mastery_notes_text = "Recent observations:\n" + "\n".join(notes_list)

    # Retrieve relevant KB chunks for grounded exercises
    kb_excerpt = ""
    try:
        from mental_gym.engine.kb_index import retrieve_chunks
        query = f"{plan.topic_name}: {plan.topic_description}"
        chunks = retrieve_chunks(store.conn, query, topic_id=plan.topic_id, limit=3)
        if chunks:
            kb_excerpt = "\n---\n".join(c["text"] for c in chunks)
    except Exception:
        pass  # KB index not available — exercises will use LLM general knowledge

    # Generate exercise
    print_exercise_header(index, total, plan.phase, ex_type.name, plan.topic_name)
    print_info("Generating exercise...")

    gen_sys, gen_usr = ex_type.generation_prompt(
        topic_name=plan.topic_name,
        topic_description=plan.topic_description,
        difficulty=plan.difficulty,
        domain=config.domain,
        mastery_notes=mastery_notes_text,
        kb_excerpt=kb_excerpt,
        secondary_topic=plan.secondary_topic_name,
    )

    prompt_text, key_points = generate_exercise(llm, gen_sys, gen_usr)

    # Display prompt
    print_prompt(prompt_text)

    # Collect response — use $EDITOR for write exercises
    exercise_start = time.time()
    use_editor = getattr(ex_type, "use_editor", False)
    if use_editor:
        print_info("Opening editor for your response... (or type inline, press Enter twice)")
        user_response = collect_response_editor(prompt_text)
    else:
        user_response = collect_response()
    exercise_duration = int(time.time() - exercise_start)

    if not user_response.strip():
        print_info("Skipped (empty response).")
        return None

    # Evaluate
    print()
    print_info("Evaluating...")

    eval_sys, eval_usr = ex_type.evaluation_prompt(
        exercise_prompt=prompt_text,
        user_response=user_response,
        key_points=key_points,
        domain=config.domain,
        mastery_notes=mastery_notes_text,
    )

    eval_result = evaluate_response(llm, eval_sys, eval_usr)

    # Display feedback
    print_feedback(
        eval_result.accuracy, eval_result.completeness,
        eval_result.depth, eval_result.overall,
        eval_result.feedback,
    )

    # Record exercise in DB
    exercise = Exercise(
        session_id=session_id,
        exercise_type=plan.exercise_type,
        topic_id=plan.topic_id,
        secondary_topic_id=plan.secondary_topic_id,
        difficulty_level=plan.difficulty,
        phase=plan.phase,
        prompt=prompt_text,
        user_response=user_response,
        score_accuracy=eval_result.accuracy,
        score_completeness=eval_result.completeness,
        score_depth=eval_result.depth,
        overall_score=eval_result.overall,
        feedback=eval_result.feedback,
        key_points=json.dumps(key_points),
        duration_seconds=exercise_duration,
    )
    exercise_id = store.insert_exercise(exercise)

    # Record mastery notes
    if eval_result.mastery_observations:
        notes = [
            MasteryNote(
                exercise_id=exercise_id,
                topic_id=plan.topic_id,
                note_type=obs.type,
                concept=obs.concept,
                detail=obs.detail,
            )
            for obs in eval_result.mastery_observations
        ]
        store.insert_mastery_notes(notes)

    # Update topic mastery + SM-2
    topic = store.get_topic(plan.topic_id)
    if topic:
        old_mastery = topic.mastery
        new_mastery = update_mastery(topic.mastery, eval_result.overall)
        sm2 = sm2_update(
            eval_result.overall, topic.sm2_interval,
            topic.sm2_easiness, topic.sm2_repetitions,
        )
        new_difficulty = max(1, min(6, plan.difficulty))  # Keep current difficulty

        store.update_topic_mastery(
            topic_id=plan.topic_id,
            mastery=new_mastery,
            difficulty_level=new_difficulty,
            sm2_interval=sm2.interval,
            sm2_easiness=sm2.easiness,
            sm2_repetitions=sm2.repetitions,
            next_review=sm2.next_review,
        )

        return {
            "overall": eval_result.overall,
            "mastery_delta": (plan.topic_name, old_mastery, new_mastery),
        }

    return {"overall": eval_result.overall}
