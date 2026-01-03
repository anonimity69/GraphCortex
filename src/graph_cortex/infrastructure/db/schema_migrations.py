from graph_cortex.infrastructure.db.neo4j_connection import get_session

# Configuration for Semantic Vector Search
# sentence-transformers (all-MiniLM-L6-v2) uses 384-dimensional vectors by default.
# If migrating to OpenAI embeddings later, change this to 1536 and re-initialize.
VECTOR_DIMENSION = 384

def initialize_schema():
    """
    Initializes constraints and indexes for the Multi-Layer Memory Framework schema.
    """
    base_queries = [
        # Working Memory Constraints
        "CREATE INDEX IF NOT EXISTS FOR (i:Interaction) ON (i.timestamp)",
        "CREATE INDEX IF NOT EXISTS FOR (m:Message) ON (m.message_id)",
        
        # Episodic Memory Constraints
        "CREATE CONSTRAINT IF NOT EXISTS FOR (e:Event) REQUIRE e.event_id IS UNIQUE",
        "CREATE INDEX IF NOT EXISTS FOR (e:Event) ON (e.timestamp)",
        
        # Semantic Memory Constraints
        "CREATE CONSTRAINT IF NOT EXISTS FOR (e:Entity) REQUIRE e.name IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Concept) REQUIRE c.name IS UNIQUE"
    ]
    
    vector_queries = [
        f"CREATE VECTOR INDEX entity_vector_index IF NOT EXISTS FOR (e:Entity) ON (e.embedding) OPTIONS {{indexConfig: {{`vector.dimensions`: {VECTOR_DIMENSION}, `similarity.function`: 'cosine'}}}}",
        f"CREATE VECTOR INDEX concept_vector_index IF NOT EXISTS FOR (c:Concept) ON (c.embedding) OPTIONS {{indexConfig: {{`vector.dimensions`: {VECTOR_DIMENSION}, `similarity.function`: 'cosine'}}}}"
    ]
    
    try:
        with get_session() as session:
            # 1. Base Constraints
            for query in base_queries:
                session.run(query)
            print("[INFO] Core Database Schema initialized successfully.")
            
            # 2. Vector Diagnostic Check
            try:
                for v_query in vector_queries:
                    session.run(v_query)
                print(f"[INFO] Vector Indexes ({VECTOR_DIMENSION}-Dimensions) initialized successfully.")
            except Exception as v_err:
                print(f"\n[WARNING] Neo4j Vector Initialization Failed.")
                print(f"[DIAGNOSTIC] Your current Neo4j Container version may be outdated and does not support Vector indexing.")
                print(f"[DIAGNOSTIC] Inner Error: {v_err}\n")
                
    except Exception as e:
        print(f"[ERROR] Failed to initialize core schema: {e}")

if __name__ == "__main__":
    initialize_schema()
