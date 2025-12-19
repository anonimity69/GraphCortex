import uuid
import sys
from graph_cortex.infrastructure.db.schema_migrations import initialize_schema
from graph_cortex.core.memory.manager import MemoryManager

def main():
    print("Welcome to GraphCortex CLI Native Interface.")
    print("Initializing Database Schema...")
    
    # This might fail gracefully if Neo4j isn't active
    initialize_schema()
    
    print("\nStarting memory integration...")
    manager = MemoryManager()
    
    session_id = f"session_{uuid.uuid4().hex[:8]}"
    
    print(f"\n[Working Memory] Processing conversation turn for session: {session_id}")
    manager.process_turn(
        session_id=session_id,
        user_input="How does clean architecture improve graph database access?",
        agent_response="By strictly decoupling the Neo4j driver queries (infrastructure) from the raw data structures (core domain), the codebase becomes modular and easily testable."
    )
    
    print("\n[Episodic & Semantic Memory] Consolidating episode...")
    summary = "User asked about Clean Architecture in graphs; agent explained decoupling driver from domain."
    extracted_entities = [
        {"entity": "Clean Architecture", "concept": "Software Design", "relation": "IS_A_PATTERN_OF"},
        {"entity": "Neo4j Driver", "concept": "Infrastructure", "relation": "BELONGS_TO_LAYER"}
    ]
    
    event_id = manager.consolidate_episode(session_id, summary, extracted_entities)
    print(f"Episode consolidated with Event ID: {event_id}")
    print("\nClean Architecture Verification Complete!")

if __name__ == "__main__":
    sys.exit(main())
