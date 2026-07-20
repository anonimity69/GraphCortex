import logging
from graph_cortex.infrastructure.db.falkordb_connection import get_graph, execute_query
from graph_cortex.config.embedding import get_vector_dimension


def initialize_schema():
    """Create indexes and vector indexes for FalkorDB. Safe to call repeatedly."""

    dim = get_vector_dimension()
    graph = get_graph()

    # --- Standard indexes ---
    index_queries = [
        "CREATE INDEX FOR (i:Interaction) ON (i.timestamp)",
        "CREATE INDEX FOR (i:Interaction) ON (i.session_id)",
        "CREATE INDEX FOR (m:Message) ON (m.message_id)",
        "CREATE INDEX FOR (m:Message) ON (m.session_id)",
        "CREATE INDEX FOR (m:Message) ON (m.uid)",
        "CREATE INDEX FOR (e:Event) ON (e.event_id)",
        "CREATE INDEX FOR (e:Event) ON (e.timestamp)",
        "CREATE INDEX FOR (e:Event) ON (e.session_id)",
        "CREATE INDEX FOR (e:Event) ON (e.uid)",
        "CREATE INDEX FOR (e:Entity) ON (e.session_id)",
        "CREATE INDEX FOR (e:Entity) ON (e.uid)",
        "CREATE INDEX FOR (c:Concept) ON (c.session_id)",
        "CREATE INDEX FOR (c:Concept) ON (c.uid)",
        "CREATE INDEX FOR (s:Searchable) ON (s.uid)",
    ]

    for q in index_queries:
        try:
            graph.query(q)
        except Exception:
            pass  # index already exists
    logging.info("Schema indexes initialized")

    # --- Fulltext index on :Searchable super-label ---
    try:
        graph.query("CALL db.idx.fulltext.createNodeIndex('Searchable', 'name')")
        logging.info("Fulltext index created on :Searchable(name)")
    except Exception:
        pass  # already exists

    # --- Vector indexes ---
    vector_queries = [
        f"CREATE VECTOR INDEX FOR (e:Entity) ON (e.embedding) OPTIONS {{dimension: {dim}, similarityFunction: 'cosine'}}",
        f"CREATE VECTOR INDEX FOR (c:Concept) ON (c.embedding) OPTIONS {{dimension: {dim}, similarityFunction: 'cosine'}}",
    ]

    for q in vector_queries:
        try:
            graph.query(q)
        except Exception:
            pass  # already exists
    logging.info(f"Vector indexes initialized ({dim}d)")

    # --- Backfill is_active for any nodes that predate soft-delete ---
    try:
        graph.query("MATCH (n) WHERE n.is_active IS NULL SET n.is_active = true")
    except Exception:
        pass

    logging.info("FalkorDB schema initialization complete")


if __name__ == "__main__":
    initialize_schema()
