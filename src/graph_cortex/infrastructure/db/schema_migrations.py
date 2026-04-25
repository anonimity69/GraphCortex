import logging
from graph_cortex.infrastructure.db.neo4j_connection import get_session
from graph_cortex.config.embedding import get_vector_dimension


def initialize_schema():
    """Create constraints, indexes, and vector indexes. Safe to call repeatedly."""
    base_queries = [
        "CREATE INDEX IF NOT EXISTS FOR (i:Interaction) ON (i.timestamp)",
        "CREATE INDEX IF NOT EXISTS FOR (m:Message) ON (m.message_id)",
        "CREATE INDEX IF NOT EXISTS FOR (m:Message) ON (m.session_id)",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (e:Event) REQUIRE e.event_id IS UNIQUE",
        "CREATE INDEX IF NOT EXISTS FOR (e:Event) ON (e.timestamp)",
        "CREATE INDEX IF NOT EXISTS FOR (e:Event) ON (e.session_id)",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (e:Entity) REQUIRE (e.name, e.session_id) IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Concept) REQUIRE (c.name, c.session_id) IS UNIQUE",
        "CREATE INDEX IF NOT EXISTS FOR (e:Entity) ON (e.session_id)",
        "CREATE INDEX IF NOT EXISTS FOR (c:Concept) ON (c.session_id)",
        "CREATE FULLTEXT INDEX hybrid_entity_concept IF NOT EXISTS FOR (n:Entity|Concept) ON EACH [n.name]",
        # backfill is_active for any nodes that predate soft-delete
        "MATCH (n) WHERE n.is_active IS NULL SET n.is_active = true"
    ]

    dim = get_vector_dimension()

    vector_queries = [
        "DROP INDEX entity_vector_index IF EXISTS",
        "DROP INDEX concept_vector_index IF EXISTS",
        f"CYPHER 25 CREATE VECTOR INDEX entity_vector_index FOR (e:Entity) ON (e.embedding) WITH [e.session_id, e.is_active] OPTIONS {{indexConfig: {{`vector.dimensions`: {dim}, `vector.similarity_function`: 'cosine'}}}}",
        f"CYPHER 25 CREATE VECTOR INDEX concept_vector_index FOR (c:Concept) ON (c.embedding) WITH [c.session_id, c.is_active] OPTIONS {{indexConfig: {{`vector.dimensions`: {dim}, `vector.similarity_function`: 'cosine'}}}}"
    ]

    try:
        with get_session() as session:
            # drop legacy single-property uniqueness constraints if they exist
            constraints = session.run("SHOW CONSTRAINTS YIELD name, labelsOrTypes, properties, type").data()
            for c in constraints:
                if c['type'] == 'UNIQUENESS' and c['properties'] == ['name'] and c['labelsOrTypes'] in [['Entity'], ['Concept']]:
                    session.run(f"DROP CONSTRAINT {c['name']}")
                    logging.info(f"Dropped legacy constraint: {c['name']}")

            for q in base_queries:
                session.run(q)
            logging.info("Schema initialized")

            try:
                for q in vector_queries:
                    session.run(q)
                logging.info(f"Vector indexes created ({dim}d)")
            except Exception as e:
                logging.warning(f"Vector index setup failed (Neo4j version may not support it): {e}")

    except Exception as e:
        logging.error(f"Schema init failed: {e}")


if __name__ == "__main__":
    initialize_schema()
