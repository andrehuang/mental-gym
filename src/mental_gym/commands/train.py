"""mental-gym train / warmup — run training sessions."""

from mental_gym.config import load_config
from mental_gym.db.schema import open_db
from mental_gym.db.store import Store
from mental_gym.engine.llm import create_backend
from mental_gym.engine.trainer import run_session
from mental_gym.ui import print_error


def run_train(args):
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

    if store.topic_count() == 0:
        print_error("No topics in database. Run 'mental-gym init' with a knowledge base first.")
        conn.close()
        return

    llm = create_backend(config.llm.backend, config.llm.model)
    focus = getattr(args, "focus", None)

    try:
        run_session(config, store, llm, focus=focus)
    finally:
        conn.close()


def run_warmup(args):
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

    if store.topic_count() == 0:
        print_error("No topics in database. Run 'mental-gym init' with a knowledge base first.")
        conn.close()
        return

    llm = create_backend(config.llm.backend, config.llm.model)

    try:
        run_session(config, store, llm, warmup_only=True)
    finally:
        conn.close()
