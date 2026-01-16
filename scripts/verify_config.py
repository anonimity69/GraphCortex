import os
import sys

# Ensure the project root is in the path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))
sys.path.append(os.path.join(PROJECT_ROOT, "src"))

from graph_cortex.config.embedding import EMBEDDING_MODEL, EMBEDDING_DEVICE, get_vector_dimension
from graph_cortex.config.retrieval import (
    RETRIEVAL_MAX_DEPTH, RETRIEVAL_CUTOFF_THRESHOLD,
    SEMANTIC_SIMILARITY_THRESHOLD, LOG_LEVEL, SHARDING_MODE
)
from graph_cortex.infrastructure.db.neo4j_connection import db_connection

def verify():
    print("=" * 60)
    print("GraphCortex — Dynamic Configuration Diagnostic")
    print("=" * 60)
    
    # 1. Configuration Check
    print(f"\n[1] CONFIGURATION LOADED:")
    print(f"    - Embedding Model:   {EMBEDDING_MODEL}")
    print(f"    - Device:            {EMBEDDING_DEVICE}")
    print(f"    - Retrieval Depth:   {RETRIEVAL_MAX_DEPTH}")
    print(f"    - Cutoff Threshold:  {RETRIEVAL_CUTOFF_THRESHOLD}")
    print(f"    - Semantic Sim Thresh: {SEMANTIC_SIMILARITY_THRESHOLD}")
    print(f"    - Log Level:         {LOG_LEVEL}")
    print(f"    - Sharding Mode:     {SHARDING_MODE}")
    
    # 2. Embedding Model Test
    print(f"\n[2] EMBEDDING MODEL TEST:")
    try:
        dim = get_vector_dimension()
        print(f"    - SUCCESS: Model loaded successfully.")
        print(f"    - Auto-Detected Dimension: {dim}")
    except Exception as e:
        print(f"    - ERROR: Failed to load embedding model: {e}")
        
    # 3. Neo4j Connection Test
    print(f"\n[3] NEO4J CONNECTIVITY TEST:")
    driver = db_connection.get_driver()
    if driver:
        try:
            with driver.session() as session:
                session.run("RETURN 1")
            print(f"    - SUCCESS: Connected to Neo4j successfully.")
        except Exception as e:
            print(f"    - ERROR: Neo4j connection failed: {e}")
    else:
        print(f"    - ERROR: Neo4j driver not initialized.")
        
    print("\n" + "=" * 60)
    print("Diagnostic Complete.")
    print("=" * 60)

if __name__ == "__main__":
    verify()
