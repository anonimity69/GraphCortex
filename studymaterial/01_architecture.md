# Module 01: Project Architecture — Why GraphCortex Exists

## The Problem GraphCortex Solves

Modern AI agents (ChatGPT, Claude, custom LLM apps) suffer from a fundamental limitation: **they have no persistent, structured memory**. Every conversation starts from scratch. Even with RAG (Retrieval-Augmented Generation), the AI retrieves isolated text chunks from a flat vector database — it cannot understand *how facts relate to each other* or *when they happened*.

### What a Flat Vector Database Does

```
User asks: "What did I say about Clean Architecture last week?"

Pinecone/Qdrant response:
  → Chunk 1: "Clean Architecture separates concerns..."
  → Chunk 2: "Infrastructure layer handles database..."
  → Chunk 3: "Domain logic should be pure..."

Problem: These are isolated paragraphs. The AI cannot deduce:
  - WHEN the user said this (chronology)
  - WHO said what (user vs agent)
  - HOW "Clean Architecture" connects to "Neo4j Driver" (topology)
```

### What GraphCortex Does

```
User asks: "What did I say about Clean Architecture last week?"

GraphCortex response:
  → Anchor: "Clean Architecture" (Entity node)
      ├── IS_A_PATTERN_OF → "Software Design" (Concept)
      ├── EXTRACTED_FROM → Event_001 (April 14, "User asked about decoupling")
      │   └── SUMMARIZES → Interaction_session_abc
      │       ├── CONTAINS → Message: "How does clean architecture improve..."
      │       └── CONTAINS → Message: "By strictly decoupling the Neo4j driver..."
      └── Connected via BFS → "Neo4j Driver" → "Infrastructure"

The AI now knows: WHO said WHAT, WHEN, and HOW concepts connect.
```

---

## The Three Memory Layers (Multi-Layer Memory Framework)

GraphCortex models memory the same way cognitive neuroscience models the human brain:

### Layer 1: Working Memory (Short-Term Buffer)
**Biological analogy:** Your brain's "scratchpad" — holds the last 7±2 items you're actively thinking about.

**In GraphCortex:** Stores the raw, real-time conversation. Each conversation session is an `Interaction` node, and each message (user or agent) is a `Message` node linked chronologically via `[:NEXT]` relationships.

```
(Interaction: session_abc)
    ├── [:CONTAINS] → (Message: "How does clean architecture...")
    │                     └── [:NEXT] → (Message: "By strictly decoupling...")
```

### Layer 2: Episodic Memory (Chronological Events)
**Biological analogy:** Your ability to remember *events* — "Last Tuesday, I had a meeting about X."

**In GraphCortex:** When a conversation ends, it gets compressed into an `Event` node with a human-readable summary. Events are chained chronologically via `[:FOLLOWS]` relationships, creating a strict timeline.

```
(Event_001: "User asked about Clean Architecture")
    ├── [:SUMMARIZES] → (Interaction: session_abc)
    └── [:FOLLOWS] → (Event_002: "User discussed Neo4j indexes")
```

### Layer 3: Semantic Memory (Facts & Knowledge)
**Biological analogy:** Your general knowledge — "Paris is the capital of France" — detached from when/where you learned it.

**In GraphCortex:** Structural facts are extracted from events. `Entity` nodes (specific things) and `Concept` nodes (abstract ideas) are linked via domain-specific relationships, and traced back to the events they were extracted from.

```
(Entity: "Clean Architecture") --[:IS_A_PATTERN_OF]--> (Concept: "Software Design")
    └── [:EXTRACTED_FROM] → (Event_001)
```

---

## Clean Architecture: The Three Tiers

### Why Not Just Write One Script?

A monolithic script mixing Neo4j queries, LLM calls, and math formulas creates "spaghetti code" that is:
- **Un-testable:** You can't test the energy decay math without spinning up a database.
- **Un-swappable:** Migrating from Neo4j to Neptune means rewriting everything.
- **Un-maintainable:** A change in one place breaks something unrelated.

### The Solution: Domain-Driven Design

```
┌─────────────────────────────────────────────────────┐
│                    INTERFACES                        │
│  (How the outside world talks to us: CLI, REST API) │
│                                                     │
│  main.py — Entry point, wires everything together   │
└─────────────────────┬───────────────────────────────┘
                      │ calls
┌─────────────────────▼───────────────────────────────┐
│                      CORE                            │
│  (Pure logic. ZERO database knowledge.)             │
│                                                     │
│  memory/manager.py    — Orchestrator                │
│  memory/working.py    — Working Memory logic        │
│  memory/episodic.py   — Episodic Memory logic       │
│  memory/semantic.py   — Semantic Memory logic       │
│  retrieval/engine.py  — Spreading Activation        │
│  retrieval/inhibition.py — Energy Decay math        │
└─────────────────────┬───────────────────────────────┘
                      │ calls
┌─────────────────────▼───────────────────────────────┐
│                 INFRASTRUCTURE                       │
│  (Physical tools. Swappable.)                       │
│                                                     │
│  db/neo4j_connection.py  — Driver singleton         │
│  db/schema_migrations.py — Constraints & indexes    │
│  db/queries/retrieval_queries.py — Raw Cypher       │
│  storage/sharding.py — Property offloading          │
└─────────────────────────────────────────────────────┘
```

### The Key Rule
**Dependencies flow DOWNWARD only.** The `core` never imports from `interfaces`. The `interfaces` never import directly from `infrastructure`. This means:

- To test the energy decay formula → No database needed.
- To switch from Neo4j to Neptune → Only modify `infrastructure/`.
- To add a REST API → Only add to `interfaces/`.

---

## Why Neo4j Instead of Pinecone/Qdrant?

| Feature | Flat Vector DB | Neo4j Graph DB |
|---|---|---|
| Nearest-neighbor search | ✅ Native | ✅ Via Vector Indexes |
| Multi-hop traversal | ❌ Manual intersection | ✅ Native BFS/DFS |
| Chronological chains | ❌ Must simulate | ✅ `[:FOLLOWS]` relationships |
| Relationship types | ❌ Metadata only | ✅ First-class `[:IS_A]`, `[:BELONGS_TO]` |
| Associative recall | ❌ Isolated chunks | ✅ Spreading Activation |
| Topological context | ❌ None | ✅ Full graph structure |

**The one-liner:** *"Vector databases are flat. Memory is not flat. Memory has topology — things connect to other things, and those connections matter."*
