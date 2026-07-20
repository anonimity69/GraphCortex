import time
import asyncio
import uuid
import uuid as uuid_lib
from pprint import pprint

from graph_cortex.infrastructure.db.schema_migrations import initialize_schema
from graph_cortex.core.memory.manager import MemoryManager
from graph_cortex.core.retrieval.engine import RetrievalEngine
from graph_cortex.core.agents.librarian import LibrarianAgent
from graph_cortex.infrastructure.db.falkordb_connection import get_graph


def generate_synthetic_data(session_id: str, num_events: int = 10):
    print(f"--- Generating Synthetic Events ---")
    manager = MemoryManager()
    start_time = time.time()
    manager.working.add_interaction(session_id)
    
    entities = [
        {"entity": "Project Orion", "concept": "Quantum Core", "relation": "REQUIRES", "properties": {"criticality": "high"}},
        {"entity": "Quantum Core", "concept": "Subspace Battery", "relation": "POWERED_BY", "properties": {"version": "v9"}},
        {"entity": "Subspace Battery", "concept": "Overheating", "relation": "HAS_ISSUE", "properties": {"temperature": "9000C"}}
    ]
    event_id = manager.consolidate_episode(session_id, "Discussed the power requirements and issues of Project Orion's core components.", entities)
    print(f"Synthetic path generation took {time.time() - start_time:.3f}s (Event ID: {event_id})")

    # Add severe noise/garbage nodes
    noise_entities = []
    print("Flooding graph with 500 dense garbage nodes...")
    for i in range(500):
        # Create some random interconnections to make the graph dense
        target_i = (i + 7) % 500
        noise_entities.append(
            {"entity": f"Noise Entity {i}", "concept": f"Noise Concept {target_i}", "relation": "DISTRACTS", "properties": {"garbage_val": i}}
        )
        
        # Batch consolidate every 100 entities to avoid massive payload slowdowns
        if (i + 1) % 100 == 0:
            manager.consolidate_episode(session_id, f"Random garbage interaction {i}", noise_entities)
            noise_entities = []
            
    if noise_entities:
        manager.consolidate_episode(session_id, "Remaining random garbage", noise_entities)
        
    print(f"Injected 500 interconnected noise entity pairs to flood the graph.")
    

async def run_benchmark():
    graph = get_graph()
    graph.query("MATCH (n) DETACH DELETE n")
    initialize_schema()
    session_id = "hard_bench"
    
    # 1. Populate
    generate_synthetic_data(session_id)
    
    engine = RetrievalEngine()
    librarian = LibrarianAgent()
    
    print("\n--- Running Latency Benchmarks ---")
    
    print("\nTesting Engine Traversal (Anchor: Project Orion)...")
    start = time.time()
    result = engine.retrieve(["Project Orion"], session_id=session_id)
    retrieval_time = time.time() - start
    print(f"Retrieval Time: {retrieval_time:.3f}s")
    
    nodes_found = [n.get("name") for n in result.get("network", [])]
    print(f"Nodes found: {nodes_found}")
    
    recall_success = any("Overheating" in str(n) for n in nodes_found)
    print(f"Recall Success: {recall_success}")
    
    print("\nTesting Librarian (RL Curation)...")
    start = time.time()
    info = await librarian.curate("The user is asking about battery issues in Project Orion.", session_id=session_id, graph_context=result)
    lib_time = time.time() - start
    print(f"Librarian Execution Time: {lib_time:.3f}s")
    print(f"Librarian Action: {info}")
    
    graph = get_graph()
    count_res = graph.query("MATCH (n) RETURN count(n)").result_set
    print(f"\nTotal Nodes in Graph: {count_res[0][0]}")

if __name__ == "__main__":
    asyncio.run(run_benchmark())
