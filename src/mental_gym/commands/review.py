"""mental-gym review — challenge yourself on your own writing."""

import json
import time
from datetime import datetime

from mental_gym.config import load_config
from mental_gym.db.schema import open_db
from mental_gym.db.store import Exercise, MasteryNote, Store
from mental_gym.engine.assessor import evaluate_response
from mental_gym.engine.llm import create_backend
from mental_gym.engine.memory import sm2_update, update_mastery
from mental_gym.engine.reviewer import (
    extract_claims_prompt, parse_claims_response, read_article,
)
from mental_gym.exercises.defend import DefendExercise
from mental_gym.ui import (
    Color, bold, collect_response, colored, dim, print_error,
    print_exercise_header, print_feedback, print_header, print_info,
    print_prompt, print_separator, print_session_summary, print_success,
)


def run_review(args):
    try:
        config = load_config(args.config)
    except FileNotFoundError as e:
        print_error(str(e))
        return

    try:
        conn = open_db(config.db_path)
    except FileNotFoundError as e:
        print_error(str(e))
        return

    store = Store(conn)
    llm = create_backend(config.llm.backend, config.llm.model)

    # Read article
    try:
        article_text = read_article(args.file)
    except FileNotFoundError as e:
        print_error(str(e))
        conn.close()
        return

    print_header(f"Mental Gym — Article Review")
    print(f"  File: {args.file}")
    print(f"  Length: {len(article_text)} chars")
    print()

    # Extract claims
    print_info("Analyzing your writing for claims and arguments...")
    topic_ids = [t.id for t in store.get_all_topics()]

    sys_prompt, usr_prompt = extract_claims_prompt(
        article_text, config.domain, topic_ids
    )

    try:
        response = llm.complete(sys_prompt, usr_prompt, json_mode=True)
        claims = parse_claims_response(response)
    except Exception as e:
        print_error(f"Failed to extract claims: {e}")
        conn.close()
        return

    if not claims:
        print_info("No challengeable claims found in the text.")
        conn.close()
        return

    print_success(f"Found {len(claims)} claims to challenge:")
    for i, c in enumerate(claims, 1):
        print(f"  {i}. [{c.claim_type}] {c.claim[:80]}...")
    print()

    # Run review session
    session_id = store.create_session(focus_topic="article_review")
    session_start = time.time()
    scores = []
    topic_deltas = {}
    exercises_done = 0
    defend_exercise = DefendExercise()

    try:
        for i, claim in enumerate(claims, 1):
            print_exercise_header(
                i, len(claims), "review",
                "Defend Your Claim", claim.claim[:50] + "..."
            )
            print_prompt(claim.challenge_prompt)

            # Collect response
            ex_start = time.time()
            user_response = collect_response()
            ex_duration = int(time.time() - ex_start)

            if not user_response.strip():
                print_info("Skipped.")
                continue

            # Evaluate using defend exercise evaluation
            print()
            print_info("Evaluating your defense...")

            key_points = [
                f"Original claim: {claim.claim}",
                f"Claim type: {claim.claim_type}",
                "Student should demonstrate deep understanding of their own argument",
            ]

            eval_sys, eval_usr = defend_exercise.evaluation_prompt(
                exercise_prompt=claim.challenge_prompt,
                user_response=user_response,
                key_points=key_points,
                domain=config.domain,
            )

            try:
                eval_result = evaluate_response(llm, eval_sys, eval_usr)
            except Exception as e:
                print_error(f"Evaluation failed: {e}")
                continue

            print_feedback(
                eval_result.accuracy, eval_result.completeness,
                eval_result.depth, eval_result.overall,
                eval_result.feedback,
            )

            scores.append(eval_result.overall)
            exercises_done += 1

            # Record exercise
            exercise = Exercise(
                session_id=session_id,
                exercise_type="review",
                topic_id=claim.related_topics[0] if claim.related_topics else "article_review",
                difficulty_level=4,  # Review is analysis-level
                phase="review",
                prompt=claim.challenge_prompt,
                user_response=user_response,
                score_accuracy=eval_result.accuracy,
                score_completeness=eval_result.completeness,
                score_depth=eval_result.depth,
                overall_score=eval_result.overall,
                feedback=eval_result.feedback,
                key_points=json.dumps(key_points),
                duration_seconds=ex_duration,
            )
            exercise_id = store.insert_exercise(exercise)

            # Record mastery notes
            if eval_result.mastery_observations:
                notes = [
                    MasteryNote(
                        exercise_id=exercise_id,
                        topic_id=claim.related_topics[0] if claim.related_topics else "article_review",
                        note_type=obs.type,
                        concept=obs.concept,
                        detail=obs.detail,
                    )
                    for obs in eval_result.mastery_observations
                ]
                store.insert_mastery_notes(notes)

            # Update mastery for related topics
            for tid in claim.related_topics:
                topic = store.get_topic(tid)
                if topic:
                    old_m = topic.mastery
                    new_m = update_mastery(topic.mastery, eval_result.overall)
                    sm2 = sm2_update(
                        eval_result.overall, topic.sm2_interval,
                        topic.sm2_easiness, topic.sm2_repetitions,
                    )
                    store.update_topic_mastery(
                        topic.id, new_m, topic.difficulty_level,
                        sm2.interval, sm2.easiness, sm2.repetitions,
                        sm2.next_review,
                    )
                    topic_deltas[topic.name] = (old_m, new_m)

    except KeyboardInterrupt:
        print()
        print_info("Review interrupted. Saving progress...")

    # Session summary
    duration = int(time.time() - session_start)
    avg_score = sum(scores) / len(scores) if scores else 0.0
    session_num = store.get_session_count()
    store.end_session(session_id, exercises_done, avg_score)

    print_session_summary(session_num, exercises_done, avg_score, duration, topic_deltas)
    conn.close()
