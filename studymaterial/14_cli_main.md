# Module 14: CLI Entry Point

## File Covered
`src/graph_cortex/interfaces/cli/main.py`

---

## What This File Does

This is the **interface layer** — where the outside world enters GraphCortex. It wires together the infrastructure (schema), core (memory + retrieval), and config (logger) into an end-to-end executable demonstration.

This file serves two purposes:
1. **Verification script** — Proves the entire system works end-to-end.
2. **Reference implementation** — Shows exactly how to use the GraphCortex API.

---

## Full Code with Line-by-Line Explanation

### Imports

```python
import uuid
import sys
import json
from graph_cortex.infrastructure.db.schema_migrations import initialize_schema
from graph_cortex.core.memory.manager import MemoryManager
from graph_cortex.core.retrieval.engine import RetrievalEngine
```

| Import | Layer | Purpose |
|---|---|---|
| `initialize_schema` | Infrastructure | Creates database constraints + vector indexes |
| `MemoryManager` | Core | Memory orchestrator API |
| `RetrievalEngine` | Core | Retrieval orchestrator API |

Notice how the CLI **only** imports from `infrastructure` (for schema setup) and `core` (for everything else). It never touches the database directly.

### The `main()` Function

#### Phase 0: Database Setup

```python
def main():
    print("Welcome to GraphCortex CLI Native Interface.")
    print("Initializing Database Schema...")
    
    # This might fail gracefully if Neo4j isn't active
    initialize_schema()
```
**Schema initialization.** Creates all constraints, indexes, and vector indexes. Safe to call multiple times (all queries use `IF NOT EXISTS`). If Neo4j is offline, it prints a warning but doesn't crash.

#### Phase 1: Working Memory — Ingesting a Conversation

```python
    print("\nStarting memory integration...")
    manager = MemoryManager()
    
    session_id = f"session_{uuid.uuid4().hex[:8]}"
```
Creates a unique session ID like `session_82dd0f7b`. The `hex[:8]` gives us the first 8 hex characters — short enough to read, unique enough to avoid collisions.

```python
    print(f"\n[Working Memory] Processing conversation turn for session: {session_id}")
    manager.process_turn(
        session_id=session_id,
        user_input="How does clean architecture improve graph database access?",
        agent_response="By strictly decoupling the Neo4j driver queries (infrastructure) from the raw data structures (core domain), the codebase becomes modular and easily testable."
    )
```
**This single call creates 3 nodes and 4 relationships:**
```
(Interaction: session_82dd0f7b)
    ├──[:CONTAINS]──→ (Message: role=user, "How does clean architecture...")
    │                     └──[:NEXT]──→
    └──[:CONTAINS]──→ (Message: role=agent, "By strictly decoupling...")
```

#### Phase 1→2 Bridge: Episodic + Semantic Memory

```python
    print("\n[Episodic & Semantic Memory] Consolidating episode...")
    summary = "User asked about Clean Architecture in graphs; agent explained decoupling driver from domain."
    extracted_entities = [
        {"entity": "Clean Architecture", "concept": "Software Design", "relation": "IS_A_PATTERN_OF"},
        {"entity": "Neo4j Driver", "concept": "Infrastructure", "relation": "BELONGS_TO_LAYER"}
    ]
    
    event_id = manager.consolidate_episode(session_id, summary, extracted_entities)
    print(f"Episode consolidated with Event ID: {event_id}")
```

**This single call triggers a cascade:**
1. Property Sharder stores the summary text
2. Episodic Memory creates an Event node and chains it chronologically
3. For each extracted entity pair:
   - Creates/updates Entity node with 768-dim embedding
   - Creates/updates Concept node with 768-dim embedding
   - Links both to the Event via `[:EXTRACTED_FROM]`
   - Creates the domain relationship (e.g., `[:IS_A_PATTERN_OF]`)

**After this call, the full Knowledge Graph looks like:**
```
(Interaction: session_82dd0f7b)
    ├── Message: user input
    ├── Message: agent response
    └── ← [:SUMMARIZES] ── (Event: "User asked about Clean Architecture...")
                                ├── ← [:EXTRACTED_FROM] ── (Entity: "Clean Architecture")
                                │                              └── [:IS_A_PATTERN_OF] → (Concept: "Software Design")
                                └── ← [:EXTRACTED_FROM] ── (Entity: "Neo4j Driver")
                                                               └── [:BELONGS_TO_LAYER] → (Concept: "Infrastructure")
```

#### Phase 2+3: Retrieval Engine — Semantic Recall

```python
    print("\n==================================")
    print("[Retrieval Engine] Testing Spreading Activation...")
    retriever = RetrievalEngine(cutoff_threshold=0.2, max_depth=3)
    
    # Search for an anchor using a synonymous term to inherently force Semantic Vector Fallback
    query = ["System Design"]
    print(f"Triggering Search for Concept: {query}")
    
    results = retriever.retrieve(query)
```

**The deliberate test:** We search for `"System Design"` — a term that does NOT exist in the graph. This forces the system through the full dual-trigger pipeline:
1. Lexical search → MISS (no node named "System Design")
2. Semantic vector fallback → HIT ("System Design" ≈ "Software Design" at cosine 0.95)
3. Spreading Activation → BFS fan-out from anchors
4. Lateral Inhibition → Filter out hubs

```python
    if results["status"] == "Hit":
        print(f"\n[ANCHORS FOUND]: {results['anchors']}")
        print(f"[ACTIVATED NETWORK]:")
        for node in results["network"]:
            print(f"  -> [{node['distance']} hops away] {node['type']}: {node['name']}")
        print(f"[INHIBITED HUBS]: {results['inhibited_hubs']}")
    else:
        print("\n[MISS] No relevant anchors found.")
```

**Expected output:**
```
[ANCHORS FOUND]: ['Software Design', 'Clean Architecture']
[ACTIVATED NETWORK]:
  -> [0 hops away] Entity: Software Design
  -> [0 hops away] Entity: Clean Architecture
  -> [2 hops away] Event: None
  -> [2 hops away] Concept: Software Design
  -> [3 hops away] Entity: Neo4j Driver
  -> [3 hops away] Concept: Infrastructure
  ...
```

```python
    print("\nPhase 3 Vector Semantic Verification Complete! Check /Logs for tracking.")

if __name__ == "__main__":
    sys.exit(main())
```

`sys.exit(main())` — `main()` returns `None` (implicitly), which maps to exit code 0 (success). If an unhandled exception occurs, Python exits with code 1.

---

## How to Use This as a Template

To add GraphCortex to your own AI agent:

```python
from graph_cortex.core.memory.manager import MemoryManager
from graph_cortex.core.retrieval.engine import RetrievalEngine

# 1. Ingest a conversation
manager = MemoryManager()
manager.process_turn(session_id="chat_001", user_input="...", agent_response="...")

# 2. Consolidate with LLM-extracted facts
manager.consolidate_episode("chat_001", summary="...", extracted_entities=[...])

# 3. Recall relevant knowledge
engine = RetrievalEngine()
results = engine.retrieve(["relevant search terms"])

# 4. Feed the activated network into your LLM's context
context = results["network"]  # Pass this to your prompt
```
