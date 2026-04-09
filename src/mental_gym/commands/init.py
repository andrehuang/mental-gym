"""mental-gym init — set up a new domain."""

import json
from pathlib import Path

from mental_gym.config import LLMConfig, MentalGymConfig, write_config
from mental_gym.db.schema import init_db
from mental_gym.db.store import Store, Topic, TopicConnection
from mental_gym.engine.llm import create_backend
from mental_gym.prompts.generation import scan_knowledge_base, topic_graph_prompt
from mental_gym.ui import (
    Color, colored, confirm, dim, print_error, print_header, print_info,
    print_separator, print_success,
)


def run_init(args):
    config_path = args.config

    if Path(config_path).exists():
        print_error(f"Config file already exists: {config_path}")
        print_info("Delete it first if you want to reinitialize.")
        return

    # Build config
    kb_path = None
    if args.knowledge_base:
        kb = Path(args.knowledge_base).resolve()
        if not kb.is_dir():
            print_error(f"Knowledge base directory not found: {kb}")
            return
        kb_path = str(kb)

    config = MentalGymConfig(
        domain=args.domain,
        knowledge_base=kb_path,
        llm=LLMConfig(backend=args.backend),
        config_dir=str(Path(config_path).resolve().parent),
    )

    # Write config
    write_config(config, config_path)
    print_success(f"Created config: {config_path}")

    # Create database
    config.resolve_paths()
    conn = init_db(config.db_path)
    store = Store(conn)
    print_success(f"Created database: {config.db_path}")

    # Scan knowledge base
    kb_summary = ""
    if kb_path:
        print_info(f"Knowledge base: {kb_path}")
        kb_summary = scan_knowledge_base(kb_path)
        md_count = kb_summary.count("\n") + (1 if kb_summary else 0)
        print_info(f"Indexed {md_count} documents from knowledge base")

    # Generate topic graph via LLM
    print()
    print_info("Generating topic graph via LLM...")
    try:
        llm = create_backend(config.llm.backend, config.llm.model)
        system, user = topic_graph_prompt(config.domain, kb_summary)
        response = llm.complete(system, user, json_mode=True)

        # Parse response — handle markdown-wrapped JSON
        text = response.strip()
        if text.startswith("```"):
            # Strip markdown code fences
            lines = text.split("\n")
            text = "\n".join(
                l for l in lines
                if not l.strip().startswith("```")
            )

        data = json.loads(text)
        topics_data = data.get("topics", [])

        if not topics_data:
            print_error("LLM returned no topics. Try again or add topics manually.")
            conn.close()
            return

        # Insert topics — if KB-backed, try to match each topic to its source file
        # so that later `mental-gym sync` doesn't create duplicates.
        kb_file_map: dict[str, tuple[str, str]] = {}
        if kb_path:
            from mental_gym.engine.kb_sync import scan_kb_files, file_hash as _fh
            from pathlib import Path
            for rel, fhash in scan_kb_files(kb_path).items():
                stem = Path(rel).stem.replace("-", "_").replace(" ", "_").lower()
                kb_file_map[stem] = (rel, fhash)

        topics = []
        for t in topics_data:
            kb_match = kb_file_map.get(t["id"])
            topics.append(Topic(
                id=t["id"],
                name=t["name"],
                description=t.get("description", ""),
                source="generated" if not kb_path else "knowledge_base",
                kb_file_path=kb_match[0] if kb_match else None,
                kb_file_hash=kb_match[1] if kb_match else None,
            ))
        store.insert_topics_batch(topics)

        # Insert connections (only for topics that exist)
        topic_ids = {t.id for t in topics}
        connections = []
        for t in topics_data:
            for conn_id in t.get("connections", []):
                if conn_id in topic_ids and t["id"] != conn_id:
                    connections.append(TopicConnection(
                        topic_a=t["id"],
                        topic_b=conn_id,
                    ))
        store.insert_connections_batch(connections)

        print_success(f"Generated {len(topics)} topics with {len(connections)} connections")

        # Show topic list
        print()
        print_header("Topic Graph")
        for t in sorted(topics, key=lambda x: x.name):
            print(f"  {colored('•', Color.CYAN)} {t.name}")
            if t.description:
                print(f"    {dim(t.description[:80])}")

    except json.JSONDecodeError as e:
        print_error(f"Failed to parse LLM response as JSON: {e}")
        print_info("Topics can be added manually with 'mental-gym add-topic'.")
    except Exception as e:
        print_error(f"LLM call failed: {e}")
        print_info("Topics can be added manually with 'mental-gym add-topic'.")

    # Build KB vector index
    if kb_path:
        try:
            from mental_gym.engine.kb_index import build_index
            print_info("Building knowledge base vector index...")
            files, chunks = build_index(conn, kb_path,
                                         progress_callback=lambda f, n: None)
            print_success(f"Indexed {files} files into {chunks} chunks for semantic search")
        except ImportError:
            print_info("Install sqlite-vec and fastembed for semantic KB search: pip install sqlite-vec fastembed")
        except Exception as e:
            print_info(f"KB indexing skipped: {e}")

    conn.close()
    print()
    print_success(f"Mental Gym initialized for domain: {args.domain}")
    print_info("Run 'mental-gym train' to start a training session.")
