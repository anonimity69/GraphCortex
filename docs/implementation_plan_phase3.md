# Phase 3 Implementation Plan: Semantic Vector Integration

This document outlines the architecture for Phase 3, which bridges the gap between text-based matching and true semantic understanding. By embedding nodes into a vector space directly inside Neo4j, the AI will be able to recall concepts even when synonyms are used (e.g., matching "System Design" to "Clean Architecture").

## Proposed Changes

### 1. Database Infrastructure Upgrades

#### [MODIFY] `src/graph_cortex/infrastructure/db/schema_migrations.py`
- Create Neo4j Vector Indexes for both `Entity` and `Concept` nodes.
- **Dynamic Dimensioning**: We will extract the vector dimension (`384`) into a clear variable at the top of the script so you can easily swap it to `1536` if you shift to OpenAI embeddings later.
- **Version Diagnostics**: We will wrap the vector creation queries in a strict `try/except` diagnostic block. If your specific Neo4j Docker image does not support Vector indexing (e.g., an outdated version), it will throw a clear timestamped error warning you rather than silently failing the whole schema.

#### [NEW / MODIFY] `src/graph_cortex/infrastructure/db/queries/retrieval_queries.py`
Add a new query function `get_anchors_by_vector_similarity(session, vector, limit)`. 
This function utilizes Neo4j's native capability `db.index.vector.queryNodes()` to find exact Anchor matches based strictly on semantic proximity (cosine similarity), returning the nodes in the exact same dictionary format as our Lexical query.

---

### 2. The Ingestion Engine (Phase 1 Bridge)

#### [MODIFY] `src/graph_cortex/core/memory/semantic.py`
- We will lazy-load `SentenceTransformer('all-MiniLM-L6-v2')`.
- Modify `add_entity()` and `extract_from_event()` so that whenever raw text is converted into an `Entity` or `Concept` node, it instantly computes the semantic array and saves it directly onto the Neo4j node under the property `embedding`.

---

### 3. The Retrieval Engine Activation (Phase 2 Bridge)

#### [MODIFY] `src/graph_cortex/core/retrieval/engine.py`
- "Un-comment" and fully activate the Phase 2 fallback stub.
- If the Lexical (BM25) trigger fails to find an exact string match for a user's query, the engine will encode the user's string into a 384-dimensional vector, pass it to our new `get_anchors_by_vector_similarity` query, and seamlessly pipe the semantic anchors right back into the Spreading Activation loop.

---

### 4. Logging and Verification

#### [NEW] `Logs/` Directory & Configuration
- We will implement a system to capture detailed timestamped analytical logs whenever the `RetrievalEngine` runs. 
- It will log to a physical `/Logs` directory (e.g., `Logs/retrieval_TIMESTAMP.log`).
- This will log EXACTLY when the Lexical search hits, when it misses, and when the Vector Fallback successfully bridges the context.

#### [MODIFY] `src/graph_cortex/interfaces/cli/main.py`
- Update `main.py` to ingest a fact about "Clean Architecture".
- Explicitly ask the engine to retrieve memory using a completely different word: "System Design".
- The script will proudly declare a `[Lexical Miss]`, fallback to Vectors, log the event to `/Logs`, and mathematically retrieve the Knowledge Graph!
