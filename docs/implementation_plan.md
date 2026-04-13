# The Distributed Neuro-Symbolic Memory Grid (NS-DMG) - Phase 1 & 2

The objective is to implement a structured, scalable graph memory foundation, moving away from flat vector databases, followed by an advanced brain-inspired retrieval engine. This plan breaks down the Low-Level Design (LLD) for Phase 1 (Execution) and outlines the architecture for Phase 2.

## User Review Required

> [!IMPORTANT]
> The exact sharding configuration in Phase 1 relies on Neo4j Fabric or application-level property sharding. For the initial phase, should we simulate property sharding at the application level (e.g., separating large text fields into a document store like MongoDB/S3 while keeping the knowledge graph in Neo4j) or set up Neo4j Enterprise Fabric (which requires licensing or specific container setups)? I will start with application-level abstractions to ensure easy local debugging with Neo4j Community Edition via Docker.

## Proposed Changes: Phase 1 (Storage Substrate)

We will build the Multi-Layer Memory Framework (MLMF) with three distinct layers using Neo4j as the Graph Database.

### 1. Infrastructure Layer

#### [NEW] `docker-compose.yml`
- Setup Neo4j instance for the graph memory.
- Configure auth credentials and expose ports `7474` (HTTP) and `7687` (Bolt).

#### [NEW] `.env` / `config.py`
- Environment variables template for database connection.

### 2. Database Connectivity & Schema

#### [NEW] `src/db/connection.py`
- Neo4j driver initialization to handle thread-safe connections.

#### [NEW] `src/db/schema.py`
- Functions to initialize Neo4j constraints (e.g., uniqueness on Semantic Entity IDs, indexing on Working Memory timestamps, and indexing on Episodic event IDs).

### 3. Core Memory Framework (MLMF)

#### [NEW] `src/memory/working_memory.py`
- `WorkingMemory` class: Handles real-time bounded interactions.
- Nodes: `Interaction`, `Message`
- Relationships: `(Interaction)-[:CONTAINS]->(Message)`, `(Message)-[:NEXT]->(Message)`

#### [NEW] `src/memory/episodic_memory.py`
- `EpisodicMemory` class: Chronological event summaries.
- Nodes: `Event`, `Summary`
- Relationships: `(Event)-[:SUMMARIZES]->(Interaction)`, `(Event)-[:FOLLOWS]->(Event)`

#### [NEW] `src/memory/semantic_memory.py`
- `SemanticMemory` class: Entity-level abstractions.
- Nodes: `Entity`, `Concept`
- Relationships: `(Entity)-[:RELATED_TO]->(Concept)`, `(Entity)-[:EXTRACTED_FROM]->(Event)`

#### [NEW] `src/memory/manager.py`
- `MemoryManager` orchestrator class exposing an API to insert a conversational turn and cascading that information across Working, Episodic, and Semantic layers.

#### [NEW] `src/memory/sharding.py`
- Abstraction layer for property sharding (distributing heavy properties away from the core graph path topology).

## Proposed Plan: Phase 2 (Retrieval Engine)

Once Phase 1 is functioning, Phase 2 implements a dynamic, brain-inspired retrieval algorithm replacing simple cosine similarity.

### 1. Dual-Trigger Initialization
- **Lexical Trigger (BM25)**: Fast graph traversal starting from string-matched Nodes.
- **Semantic Trigger (Dense Vector)**: Neo4j Vector Index search for finding conceptual anchor nodes when terms don't match exactly.

### 2. Spreading Activation Algorithm
- Use Neo4j Graph Data Science (GDS) or custom Python traversal to implement energy propagation from the anchor nodes outward.
- Apply a "Fan Effect" (attenuation factor based on node degree) where nodes with hundreds of relationships dilute the activation energy faster than specific, low-degree nodes.

### 3. Lateral Inhibition & Gating
- Apply filtering logic during graph traversal. If a generic hub node is activated alongside a highly specific node, the specific node inhibits the hub node to prevent flooding the context window (Hub Explosion problem).

## Open Questions

1. **Docker Setup**: Should I configure the Neo4j container to initialize the APOC (Awesome Procedures On Cypher) and GDS (Graph Data Science) plugins right away, as we'll need GDS for Phase 2 spreading activation?
2. **Embeddings**: For the Semantic Trigger in Phase 2, which embedding model should we design the schema vector sizes for (e.g., OpenAI `text-embedding-3-small` (1536 dims), or local HuggingFace BGE/MiniLM)?

## Verification Plan

### Automated Tests
- Unit tests mapping a dummy conversation through `MemoryManager`.
- Graph assertions verifying Neo4j node structures via a test container.

### Manual Verification
- We can connect to `http://localhost:7474`, run a seeded script, and visually inspect the Multi-Layer topology in the Neo4j Browser to ensure relationships accurately depict Working, Episodic, and Semantic linkages.
