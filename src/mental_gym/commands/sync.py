"""mental-gym sync — sync knowledge base changes."""

from mental_gym.config import load_config
from mental_gym.db.schema import open_db
from mental_gym.db.store import Store
from mental_gym.engine.kb_sync import apply_sync, detect_changes, retire_deleted
from mental_gym.ui import (
    Color, bold, colored, confirm, dim, print_error, print_header,
    print_info, print_separator, print_success,
)


def run_sync(args):
    try:
        config = load_config(args.config)
    except FileNotFoundError as e:
        print_error(str(e))
        return

    if not config.knowledge_base:
        print_error("No knowledge base configured. Nothing to sync.")
        return

    try:
        conn = open_db(config.db_path)
    except FileNotFoundError as e:
        print_error(str(e))
        return

    store = Store(conn)

    print_header("Knowledge Base Sync")
    print(f"  KB path: {config.knowledge_base}")
    print()

    new_files, modified_files, deleted_files = detect_changes(
        store, config.knowledge_base
    )

    if not new_files and not modified_files and not deleted_files:
        print_success("Knowledge base is up to date. No changes detected.")
        conn.close()
        return

    # Report changes
    if new_files:
        print(bold(f"  New files ({len(new_files)}):"))
        for f in new_files:
            print(f"    {colored('+', Color.GREEN)} {f}")
    if modified_files:
        print(bold(f"  Modified files ({len(modified_files)}):"))
        for f in modified_files:
            print(f"    {colored('~', Color.YELLOW)} {f}")
    if deleted_files:
        print(bold(f"  Deleted files ({len(deleted_files)}):"))
        for f in deleted_files:
            print(f"    {colored('-', Color.RED)} {f}")
    print()

    # Confirm
    total_changes = len(new_files) + len(modified_files) + len(deleted_files)
    if total_changes > 0:
        if confirm(f"Apply {total_changes} changes?"):
            added, updated = apply_sync(store, config.knowledge_base,
                                         new_files, modified_files)
            retired = 0
            if deleted_files:
                retired = retire_deleted(store, deleted_files)
            parts = []
            if added:
                parts.append(f"{added} topics added")
            if updated:
                parts.append(f"{updated} updated")
            if retired:
                parts.append(f"{retired} retired")
            print_success(f"Sync complete: {', '.join(parts) or 'no changes'}.")

            # Update vector index
            try:
                from mental_gym.engine.kb_index import build_index
                print_info("Updating vector index...")
                files, chunks = build_index(conn, config.knowledge_base)
                print_success(f"Re-indexed {files} files ({chunks} chunks)")
            except ImportError:
                pass
            except Exception as e:
                print_info(f"Index update skipped: {e}")
        else:
            print_info("Sync cancelled.")

    conn.close()
