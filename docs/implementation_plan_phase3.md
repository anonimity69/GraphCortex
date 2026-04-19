# Phase 3 Implementation Plan: Distributed Orchestration (Ray)

This document outlines the architecture for Phase 3, which transitions the GraphCortex system into a decoupled, distributed multi-agent infrastructure (as described in the true NS-DMG blueprint), alongside a critical storage substrate upgrade.

*(Note: The previous "Semantic Vector Integration" works have been retroactively consolidated into Phase 2 of the true architectural progression).*

## Proposed Changes

### 1. Global Soft-Deletions
To prepare for Phase 4 (where RL agents will curate memory autonomously), we must modify the schema so that graph elements are never physically deleted (which breaks historical tracking). Instead, they should be deactivated and mathematically skipped during retrieval.

#### [MODIFY] `src/graph_cortex/infrastructure/db/schema_migrations.py`
- Add an initialization query to default legacy nodes to `is_active: true` via a retro-active Cypher fallback query.

#### [MODIFY] `src/graph_cortex/infrastructure/db/queries/retrieval_queries.py`
- Enforce an `AND coalesce(node.is_active, true) = true` check on the native Spreading Activation recursive Cypher matches (`execute_spreading_activation_hop`).
- Ensure vector baseline fallback search and lexical trigges also skip deactivated nodes.

#### [NEW] `src/graph_cortex/core/memory/curation.py`
- Create a core module that encapsulates a `set_node_active_status` function, allowing future librarian bots to execute target-deactivation safely.

---

### 2. Ray Cluster Infrastructure

#### [MODIFY] `docker-compose.yml`
- Add `ray-head` and `ray-worker` services to run alongside the Neo4j instance to enable scalable cluster computing.

#### [NEW] `src/graph_cortex/infrastructure/inference/llm_router.py`
- Build a highly scalable Ray Serve Deployment (`LLMEngineDeployment`) that encapsulates the `gemini-2.0-flash` calls completely independently from the core orchestration layers.

---

### 3. Multi-Agent Scaffolding

#### [NEW] `src/graph_cortex/core/agents/base_agent.py`
- Establish a foundational Python Class that binds to the local Ray cluster and acts as the asynchronous bridging API for the agents to hit the LLM Router.

#### [NEW] `src/graph_cortex/core/agents/researcher.py`
- **The Research Agent:** Responsible for triggering the dual-search `RetrievalEngine` to find the topological state and requesting LLM response generations based strictly on the retrieved vector bounds.

#### [NEW] `src/graph_cortex/core/agents/summarizer.py`
- **The Summary Agent:** Responsible for running strictly structured JSON extractions on the generated conversations resulting into `(Entity)-[REL]->(Concept)` triples.

#### [MODIFY] `src/graph_cortex/interfaces/cli/main.py`
- Refactor the execution flow to be natively `async`. Bind the agents, load the context natively, and execute the multi-agent routines concurrently.
