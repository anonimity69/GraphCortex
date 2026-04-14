# Phase 2 Implementation Plan: The Retrieval Engine

This document outlines the Low-Level Design (LLD) for building the Spreading Activation Retrieval Engine in GraphCortex. This engine will allow the AI to actively recall relevant memories without suffering from finding too many generic concepts (the "Hub Explosion" problem).

## Proposed Changes

Because we are following Clean Architecture, our retrieval engine will be separated strictly between `core` (the math/theory) and `infrastructure` (the actual Neo4j retrieval execution).

---

### 1. The Core Retrieval Logic

The core logic handles the theory of how energy spreads and fades (attenuates) over time.

#### `src/graph_cortex/core/retrieval/engine.py`
We will build the `RetrievalEngine` class here. It will be the "Brain" for recalling information.
- Implement **Dual-Trigger routing**: It will start a search using exact keywords (Lexical) or vector similarity (Semantic) via `sentence-transformers`.
- Implement **Energy Decay (The Fan Effect)**: As traversal hops outward, the activation energy will decay based on distance (`depth_limit = 3`) and the node's degree (hub nodes diffuse energy faster).

#### `src/graph_cortex/core/retrieval/inhibition.py`
A module strictly designed to handle **Lateral Inhibition**. 
- It will filter out overly generic tokens. For example, if "User", "AI", and "Project" nodes get activated, this logic will automatically suppress them to prevent flooding the LLM's context window.

---

### 2. The Infrastructure Execution

This layer will take the theories above and execute them against the Neo4j database natively for maximum scalable professionalism.

#### `src/graph_cortex/infrastructure/db/queries/retrieval_queries.py`
- Expose precise, parameterized Cypher blocks that calculate paths up to depth 3 and return distance/degree metrics necessary for the energy decay formulas in the core layer.
- Ensure the queries are scalable and shippable.

#### `src/graph_cortex/infrastructure/db/neo4j_connection.py`
- Provide `execute_read_query()` methods capable of executing read-only transactional queries safely and efficiently.

---

### 3. Interface Integration

#### `src/graph_cortex/interfaces/cli/main.py`
- We will update our verification script. After `consolidate_episode` stores our mock memory, we ask a generic query and ensure the `RetrievalEngine` mathematically lights up the right nodes and returns the exact correct sub-graph context.

## Approved Specifications
- **Neo4j Target**: Scalable, shippable approach focusing on dedicated abstraction points.
- **Embedded Vectors**: Stick to `sentence-transformers` locally to avoid external API dependencies and costs.
- **Traversal limits**: Cap the BFS at `depth=3` and mathematically integrate an energy decay factor.

## Verification Plan

### Automated Tests
- We will write a specific mathematical test inside `tests/` to guarantee that "Hub Nodes" correctly dilute energy compared to isolated, highly specific nodes.

### Manual Verification
- We will run the updated CLI script.
- We will open the `Neo4j Browser` at `localhost:7474` and use visual queries to ensure the paths returned by our python code match the physical reality in the database.
