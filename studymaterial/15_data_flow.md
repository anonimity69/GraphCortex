# Module 15: End-to-End Data Flow Walkthrough

## The Complete Journey of a Single Conversation

This module traces the **exact path** that data takes through the entire GraphCortex system, from the moment a user sends a message to the moment the AI recalls it using a synonym.

---

## Act 1: The Conversation Happens

**User says:** *"How does clean architecture improve graph database access?"*  
**Agent says:** *"By strictly decoupling the Neo4j driver queries (infrastructure) from the raw data structures (core domain), the codebase becomes modular and easily testable."*

### Call Chain:

```
main.py
  └→ MemoryManager.process_turn()
       ├→ WorkingMemory.add_interaction("session_82dd")
       │    └→ Neo4j: MERGE (i:Interaction {session_id: "session_82dd"})
       │
       ├→ WorkingMemory.add_message("session_82dd", "user", "How does...")
       │    └→ Neo4j: MATCH (i) → CREATE (m:Message) → CREATE (i)-[:CONTAINS]->(m)
       │              No previous message → FOREACH skips [:NEXT] creation
       │
       └→ WorkingMemory.add_message("session_82dd", "agent", "By strictly...")
            └→ Neo4j: MATCH (i) → CREATE (m2:Message) → CREATE (i)-[:CONTAINS]->(m2)
                      Found previous message m1 → FOREACH creates (m1)-[:NEXT]->(m2)
```

### Neo4j State After Act 1:

```
┌─────────────────────────────────────────────┐
│             WORKING MEMORY                   │
│                                             │
│  (Interaction: session_82dd)                │
│       │                                     │
│       ├──[:CONTAINS]──→ (Message: user)     │
│       │                    │                │
│       │                    └── [:NEXT] ──→  │
│       │                                     │
│       └──[:CONTAINS]──→ (Message: agent)    │
│                                             │
│  Total: 3 nodes, 4 relationships            │
└─────────────────────────────────────────────┘
```

---

## Act 2: The Episode Gets Consolidated

**An LLM generates a summary and extracts structured facts.**

### Call Chain:

```
main.py
  └→ MemoryManager.consolidate_episode()
       │
       ├→ PropertySharder.store("ep_session_82dd", "User asked about...")
       │    └→ Mode: local → returns the string unchanged
       │
       ├→ EpisodicMemory.create_event("session_82dd", "User asked about...")
       │    └→ Neo4j: MATCH (i:Interaction) → CREATE (e:Event)
       │              CREATE (e)-[:SUMMARIZES]->(i)
       │              No previous event → FOREACH skips [:FOLLOWS]
       │              RETURN event_id = "45a3e13b-..."
       │
       ├→ SemanticMemory.add_entity("Clean Architecture")
       │    ├→ _get_embedding("Clean Architecture")
       │    │    └→ SentenceTransformer('bge-base-en-v1.5', device='mps')
       │    │       └→ encode() → [0.031, -0.089, 0.124, ...] (768 floats)
       │    └→ Neo4j: MERGE (e:Entity {name: "Clean Architecture"})
       │              SET e.embedding = [0.031, -0.089, ...]
       │
       ├→ SemanticMemory.add_entity("Software Design")
       │    ├→ _get_embedding("Software Design")
       │    │    └→ (model already loaded — cache hit)
       │    │       └→ encode() → [0.042, -0.076, 0.118, ...] (768 floats)
       │    └→ Neo4j: MERGE (e:Entity {name: "Software Design"})
       │              SET e.embedding = [0.042, -0.076, ...]
       │
       └→ SemanticMemory.extract_from_event(event_id, "Clean Architecture", "Software Design", "IS_A_PATTERN_OF")
            └→ Neo4j: MATCH (ev:Event {event_id: "45a3e13b-..."})
                      MERGE (e:Entity {name: "Clean Architecture"})
                      SET e.embedding = $entity_vector
                      MERGE (c:Concept {name: "Software Design"})
                      SET c.embedding = $concept_vector
                      MERGE (e)-[:EXTRACTED_FROM]->(ev)
                      MERGE (c)-[:EXTRACTED_FROM]->(ev)
                      MERGE (e)-[:IS_A_PATTERN_OF]->(c)
```

### Neo4j State After Act 2:

```
┌──────────────────────────────────────────────────────────────────────┐
│                                                                      │
│  ┌─ WORKING MEMORY ──────────┐     ┌─ EPISODIC MEMORY ─────────┐   │
│  │ (Interaction: session_82dd)│     │ (Event: "User asked about  │   │
│  │    ├── Message: user       │←────│  Clean Architecture...")    │   │
│  │    └── Message: agent      │  [:SUMMARIZES]                   │   │
│  └────────────────────────────┘     └────────────┬───────────────┘   │
│                                                  │                    │
│                                    [:EXTRACTED_FROM]                  │
│                                                  │                    │
│  ┌─ SEMANTIC MEMORY ────────────────────────────┼────────────────┐   │
│  │                                               │                │   │
│  │  (Entity: "Clean Architecture")  ←────────────┘                │   │
│  │     embedding: [0.031, -0.089, ...]                            │   │
│  │         │                                                      │   │
│  │         └── [:IS_A_PATTERN_OF] ──→ (Concept: "Software Design")│   │
│  │                                     embedding: [0.042, -0.076] │   │
│  │                                                                │   │
│  │  (Entity: "Neo4j Driver")                                     │   │
│  │     embedding: [0.055, -0.023, ...]                            │   │
│  │         │                                                      │   │
│  │         └── [:BELONGS_TO_LAYER] ──→ (Concept: "Infrastructure")│   │
│  │                                     embedding: [-0.011, 0.089] │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  Total: 9 nodes, 11 relationships, 4 vector embeddings              │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Act 3: The AI Recalls Using a Synonym

**User searches for:** *"System Design"* (this exact string does NOT exist in the graph)

### Call Chain:

```
main.py
  └→ RetrievalEngine.retrieve(["System Design"])
       │
       ├→ STEP 1A: get_anchor_nodes_by_name(session, ["System Design"])
       │    └→ Neo4j: MATCH (n) WHERE n.name CONTAINS "System Design"
       │       Result: [] ← LEXICAL MISS
       │
       ├→ Logger: "Lexical Miss for '['System Design']'"
       │
       ├→ STEP 1B: Semantic Vector Fallback
       │    ├→ SentenceTransformer.encode("System Design")
       │    │    └→ MPS GPU: [0.039, -0.082, 0.121, ...] (768 floats)
       │    │
       │    └→ get_anchors_by_vector_similarity(session, vector, limit=2)
       │         └→ Neo4j: CALL db.index.vector.queryNodes('entity_vector_index', 2, $vector)
       │            HNSW search across all Entity embeddings
       │            
       │            Cosine("System Design", "Software Design")  = 0.9484 ✅ > 0.65
       │            Cosine("System Design", "Clean Architecture") = 0.8224 ✅ > 0.65
       │            Cosine("System Design", "Neo4j Driver")     = 0.3102 ❌ < 0.65
       │            Cosine("System Design", "Infrastructure")   = 0.4891 ❌ < 0.65
       │            
       │            Result: [{"name": "Software Design", "score": 0.9484},
       │                     {"name": "Clean Architecture", "score": 0.8224}]
       │
       ├→ Logger: "Semantic Fallback Success! Found semantic anchors: [...]"
       │
       ├→ STEP 2: Spreading Activation (for each anchor)
       │    │
       │    ├→ Anchor: "Software Design" (AE = 1.0)
       │    │    └→ execute_spreading_activation_hop(session, node_id, depth=3)
       │    │         └→ Neo4j: MATCH path = (start)-[*1..3]-(connected)
       │    │            Returns: Event_001 (dist=2, deg=5), Interaction (dist=3, deg=4), ...
       │    │
       │    └→ Anchor: "Clean Architecture" (AE = 1.0)
       │         └→ execute_spreading_activation_hop(session, node_id, depth=3)
       │              └→ Neo4j: MATCH path = (start)-[*1..3]-(connected)
       │                 Returns: Software Design (dist=2, deg=3), Event_001 (dist=2, deg=5), ...
       │
       ├→ STEP 3: Lateral Inhibition (for each anchor's network)
       │    └→ apply_lateral_inhibition(traversed_nodes, cutoff_threshold=0.2)
       │         For each node:
       │           AE = 1.0 / (((dist × 0.5) + 1) × ((deg × 0.1) + 1))
       │           Keep if AE >= 0.2, otherwise inhibit
       │
       └→ STEP 4: Deduplicate overlapping networks
            └→ Merge by node_id, keep highest AE
               Return final activated knowledge sub-graph
```

### The Final Output:

```python
{
    "status": "Hit",
    "anchors": ["Software Design", "Clean Architecture"],
    "network": [
        {"name": "Software Design",    "type": "Entity",      "distance": 0, "AE": 1.0},
        {"name": "Clean Architecture",  "type": "Entity",      "distance": 0, "AE": 1.0},
        {"name": "Software Design",     "type": "Concept",     "distance": 2, "AE": 0.36},
        {"name": "Neo4j Driver",        "type": "Entity",      "distance": 3, "AE": 0.33},
        {"name": "Infrastructure",      "type": "Concept",     "distance": 3, "AE": 0.33},
        ...
    ],
    "inhibited_hubs": [...]
}
```

---

## The Key Insight

The user searched for **"System Design"**. This string appears NOWHERE in the database. Yet the system:

1. Recognised that "System Design" is **semantically similar** to "Software Design" (0.95 cosine)
2. Also found "Clean Architecture" as a related anchor (0.82 cosine)
3. Traversed outward to discover the full connected knowledge network
4. Filtered out irrelevant hubs
5. Returned a rich, structured sub-graph the AI can reason over

**This is the difference between "searching for text" and "understanding meaning."**

---

## Summary: The Full Technology Stack

```
┌─────────────────────────────────────────────────────────┐
│                     USER INPUT                           │
│                  "System Design"                         │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│               BAAI/bge-base-en-v1.5                      │
│            (109M params, 768-dim output)                 │
│              Apple Silicon MPS GPU                       │
└────────────────────────┬────────────────────────────────┘
                         │ 768-dim vector
                         ▼
┌─────────────────────────────────────────────────────────┐
│              Neo4j 5.x Vector Index                      │
│            HNSW + Cosine Similarity                      │
│        entity_vector_index (768-dim)                     │
└────────────────────────┬────────────────────────────────┘
                         │ Anchor nodes
                         ▼
┌─────────────────────────────────────────────────────────┐
│          Neo4j Cypher BFS Traversal                      │
│         Variable-length paths [*1..3]                    │
│         Returns distance + degree                        │
└────────────────────────┬────────────────────────────────┘
                         │ Raw network
                         ▼
┌─────────────────────────────────────────────────────────┐
│           Lateral Inhibition (Python)                    │
│    AE = E / ((dist_factor) × (degree_factor))           │
│         cutoff_threshold = 0.2                           │
└────────────────────────┬────────────────────────────────┘
                         │ Filtered network
                         ▼
┌─────────────────────────────────────────────────────────┐
│            Activated Knowledge Sub-Graph                  │
│                                                          │
│   Ready to be injected into an LLM's context window     │
└─────────────────────────────────────────────────────────┘
```
