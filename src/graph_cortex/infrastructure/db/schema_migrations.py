from graph_cortex.infrastructure.db.neo4j_connection import get_session
from graph_cortex.config.embedding import get_vector_dimension
import logging

def initialize_schema():
    """
    Initializes constraints and indexes for the Multi-Layer Memory Framework schema.
    """
    base_queries = [
        # Working Memory Constraints
        "CREATE INDEX IF NOT EXISTS FOR (i:Interaction) ON (i.timestamp)",
        "CREATE INDEX IF NOT EXISTS FOR (m:Message) ON (m.message_id)",
        "CREATE INDEX IF NOT EXISTS FOR (m:Message) ON (m.session_id)",
        
        # Episodic Memory Constraints
        "CREATE CONSTRAINT IF NOT EXISTS FOR (e:Event) REQUIRE e.event_id IS UNIQUE",
        "CREATE INDEX IF NOT EXISTS FOR (e:Event) ON (e.timestamp)",
        "CREATE INDEX IF NOT EXISTS FOR (e:Event) ON (e.session_id)",
        
        # Semantic Memory Constraints (Composite uniqueness for namespacing)
        "CREATE CONSTRAINT IF NOT EXISTS FOR (e:Entity) REQUIRE (e.name, e.session_id) IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Concept) REQUIRE (c.name, c.session_id) IS UNIQUE",
        "CREATE INDEX IF NOT EXISTS FOR (e:Entity) ON (e.session_id)",
        "CREATE INDEX IF NOT EXISTS FOR (c:Concept) ON (c.session_id)",
        
        # Fulltext Lexical Search (Hybrid Engine)
        "CREATE FULLTEXT INDEX hybrid_entity_concept IF NOT EXISTS FOR (n:Entity|Concept) ON EACH [n.name]",
        
        # Global Soft Delete Backfill
        "MATCH (n) WHERE n.is_active IS NULL SET n.is_active = true"
    ]
    
    # Auto-detect vector dimension from the configured model
    dim = get_vector_dimension()
    
    vector_queries = [
        "DROP INDEX entity_vector_index IF EXISTS",
        "DROP INDEX concept_vector_index IF EXISTS",
        f"CYPHER 25 CREATE VECTOR INDEX entity_vector_index FOR (e:Entity) ON (e.embedding) WITH [e.session_id, e.is_active] OPTIONS {{indexConfig: {{`vector.dimensions`: {dim}, `vector.similarity_function`: 'cosine'}}}}",
        f"CYPHER 25 CREATE VECTOR INDEX concept_vector_index FOR (c:Concept) ON (c.embedding) WITH [c.session_id, c.is_active] OPTIONS {{indexConfig: {{`vector.dimensions`: {dim}, `vector.similarity_function`: 'cosine'}}}}"
    ]
    
    try:
        with get_session() as session:
            # 0. Drop legacy constraints if they exist (searching by property signature)
            constraints = session.run("SHOW CONSTRAINTS YIELD name, labelsOrTypes, properties, type").data()
            for c in constraints:
                # If it's a uniqueness constraint on just 'name', it's legacy
                if c['type'] == 'UNIQUENESS' and c['properties'] == ['name'] and c['labelsOrTypes'] in [['Entity'], ['Concept']]:
                    session.run(f"DROP CONSTRAINT {c['name']}")
                    logging.info(f"Dropped legacy constraint: {c['name']}")

            # 1. Base Constraints
            for query in base_queries:
                session.run(query)
            logging.info("Core Database Schema initialized successfully.")
            
            # 2. Vector Diagnostic Check
            try:
                for v_query in vector_queries:
                    session.run(v_query)
                logging.info(f"Vector Indexes ({dim}-Dimensions) initialized successfully.")
            except Exception as v_err:
                logging.warning("Neo4j Vector Initialization Failed.")
                logging.warning("Your current Neo4j Container version may be outdated and does not support Vector indexing.")
                logging.warning(f"Inner Error: {v_err}")
                
    except Exception as e:
        logging.error(f"Failed to initialize core schema: {e}")

if __name__ == "__main__":
    initialize_schema()
