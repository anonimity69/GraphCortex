from graph_cortex.infrastructure.db.neo4j_connection import get_session

def initialize_schema():
    """
    Initializes constraints and indexes for the Multi-Layer Memory Framework schema.
    """
    queries = [
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
    
    try:
        with get_session() as session:
            for query in queries:
                session.run(query)
            print("Schema initialized successfully.")
    except Exception as e:
        print(f"Failed to initialize schema: {e}")

if __name__ == "__main__":
    initialize_schema()
