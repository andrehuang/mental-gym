"""mental-gym status — show progress dashboard."""

from mental_gym.config import load_config
from mental_gym.db.schema import open_db
from mental_gym.db.store import Store
from mental_gym.ui import bold, colored, Color, dim, print_header, print_separator


def run_status(args):
    config = load_config(args.config)
    conn = open_db(config.db_path)
    store = Store(conn)

    topic_count = store.topic_count()
    session_count = store.get_session_count()

    print_header(f"Mental Gym — {config.domain}")
    print_separator()
    print(f"  Topics: {topic_count}  |  Sessions: {session_count}  |  Backend: {config.llm.backend}")
    print()

    if topic_count == 0:
        print(dim("  No topics yet. Run 'mental-gym init' with a knowledge base, or use 'mental-gym add-topic'."))
        conn.close()
        return

    # Topic mastery overview
    topics = store.get_all_topics()
    print(bold("  Topic Mastery:"))
    for t in topics:
        mastery_pct = f"{t.mastery:.0%}"
        if t.mastery >= 0.75:
            bar_color = Color.GREEN
        elif t.mastery >= 0.4:
            bar_color = Color.YELLOW
        else:
            bar_color = Color.RED

        bar_len = int(t.mastery * 20)
        bar = colored("█" * bar_len, bar_color) + dim("░" * (20 - bar_len))
        tested = f"({t.times_tested}x)" if t.times_tested > 0 else "(new)"

        print(f"    {bar} {mastery_pct:>4}  {t.name}  {dim(tested)}")

    # Due for review
    due = store.get_topics_due_for_review()
    if due:
        print()
        print(bold(f"  Due for review ({len(due)}):"))
        for t in due[:5]:
            print(f"    - {t.name}")

    # Recent sessions
    recent = store.get_recent_sessions(limit=3)
    if recent:
        print()
        print(bold("  Recent Sessions:"))
        for s in recent:
            duration = f"{s.duration_seconds // 60}m" if s.duration_seconds else "?"
            score = f"{s.avg_score:.1f}/5" if s.avg_score else "—"
            print(f"    #{s.id}  {s.started_at[:10]}  {duration}  {score}  ({s.exercise_count} exercises)")

    print()
    conn.close()
