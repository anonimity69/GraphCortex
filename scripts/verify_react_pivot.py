import asyncio
import logging
from graph_cortex.core.memory.semantic import SemanticMemory
from graph_cortex.core.rl.action_env import GraphMemoryEnv
from graph_cortex.infrastructure.db.neo4j_connection import get_session

async def verify_react_pivot_protection():
    """
    Simulates the 'React -> SvelteKit' pivoting scenario and verifies that the 
    Librarian cannot destructively update the historical 'React' fact.
    """
    print("\n--- Manual Verification: React -> SvelteKit Pivot Protection ---")
    
    semantic = SemanticMemory()
    env = GraphMemoryEnv()
    
    # 1. Create the initial fact node (Fact: React is the frontend)
    print("[1/4] Establishing historical fact: Component: 'React'")
    semantic.add_entity(name="React", node_type="Component", attributes={"purpose": "Frontend library"})
    
    # Get the elementId of the node for the update attempt
    with get_session() as session:
        result = session.run("MATCH (n:Component {name: 'React'}) RETURN elementId(n) as id")
        record = result.single()
        if not record:
            print("Error: Could not find React node in DB.")
            return
        node_id = record["id"]
        print(f"      Node ID: {node_id}")

    # 2. Simulate the Librarian's attempt to overwrite React with SvelteKit
    print("[2/4] Librarian attempting Destructive Update: rename 'React' to 'SvelteKit'...")
    action = 2 # UPDATE
    kwargs = {
        "node_id": node_id,
        "properties": {
            "name": "SvelteKit",
            "purpose": "Consolidated Framework",
            "curation_note": "Migrated from React"
        }
    }
    
    # Execute the step in the action environment
    state, reward, done, truncated, info = env.step(action, kwargs)
    
    # 3. Verify the Violation was caught
    print(f"[3/4] Checking Environment Response: {info['status']}")
    if "action_violation" in info:
        print(f"      Violation Logged: {info['action_violation']}")
    else:
        print("      FAIL: No violation was logged in the info dictionary.")

    # 4. Verify the Database State
    with get_session() as session:
        result = session.run("MATCH (n) WHERE elementId(n) = $node_id RETURN n.name as name, n.purpose as purpose, n.curation_note as note", node_id=node_id)
        record = result.single()
        
        print(f"[4/4] Final Database Check for Node {node_id}:")
        print(f"      Current Name: {record['name']}")
        print(f"      Current Purpose: {record['purpose']}")
        print(f"      Curation Note: {record['note']}")
        
        if record['name'] == "React":
            print("\n✅ SUCCESS: The historical 'React' name was protected from overwriting!")
        else:
            print("\n❌ FAILURE: The node was successfully renamed to SvelteKit. Immutability failed.")

if __name__ == "__main__":
    asyncio.run(verify_react_pivot_protection())
