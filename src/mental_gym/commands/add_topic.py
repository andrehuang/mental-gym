"""mental-gym add-topic — add a new topic to the graph."""

import json
from datetime import datetime

from mental_gym.config import load_config
from mental_gym.db.schema import open_db
from mental_gym.db.store import Store, Topic, TopicConnection
from mental_gym.engine.llm import create_backend
from mental_gym.ui import (
    Color, colored, dim, print_error, print_info, print_success,
)


def run_add_topic(args):
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
    topic_name = args.name

    # Generate topic ID
    topic_id = topic_name.lower().replace(" ", "_").replace("-", "_")
    topic_id = "".join(c for c in topic_id if c.isalnum() or c == "_")

    # Check if exists
    if store.get_topic(topic_id):
        print_error(f"Topic '{topic_id}' already exists.")
        conn.close()
        return

    # Use LLM to generate description and connections
    existing_topics = store.get_all_topics()
    existing_ids = [t.id for t in existing_topics]

    llm = create_backend(config.llm.backend, config.llm.model)

    system = f"""You are an expert in {config.domain}. Generate a brief description
and identify connections for a new topic being added to a study curriculum.
Respond with valid JSON only."""

    existing_list = ", ".join(existing_ids[:40]) if existing_ids else "(none yet)"
    user = f"""New topic: {topic_name}
Existing topics in the graph: {existing_list}

Return JSON:
{{
  "description": "1-2 sentence description of this topic",
  "connections": ["existing_topic_id_1", "existing_topic_id_2"]
}}

Only include connections to topics that actually exist in the list above."""

    try:
        print_info("Generating topic details...")
        response = llm.complete(system, user, json_mode=True)
        text = response.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(l for l in lines if not l.strip().startswith("```"))
        data = json.loads(text)

        description = data.get("description", "")
        connections = data.get("connections", [])
    except Exception as e:
        print_info(f"LLM unavailable ({e}). Adding topic without description.")
        description = ""
        connections = []

    # Insert topic
    topic = Topic(
        id=topic_id,
        name=topic_name,
        description=description,
        source="user",
        created_at=datetime.utcnow().isoformat(),
    )
    store.insert_topic(topic)

    # Insert connections (only to existing topics)
    existing_set = set(existing_ids)
    valid_connections = [c for c in connections if c in existing_set]
    for cid in valid_connections:
        store.insert_connection(TopicConnection(topic_id, cid))

    print_success(f"Added topic: {topic_name}")
    if description:
        print(f"  {dim(description)}")
    if valid_connections:
        print(f"  Connected to: {', '.join(valid_connections)}")

    conn.close()
