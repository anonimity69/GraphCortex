# Architecture Decisions

## FalkorDB over Neo4j
Neo4j's JVM-based architecture caused 30-45s cold starts, clunky node deletion (constraint cascade issues), and limited visualization. FalkorDB (GraphBLAS engine, Redis-based) gives us sub-second startup, single-container Docker deployment with built-in browser UI, and the sparse matrix representation is architecturally ideal for spreading activation traversals. Cypher compatibility is ~95%, so migration was clean.

## A* retrieval over blind BFS
The original spreading activation used breadth-first expansion, treating all neighbors equally. Now the Researcher uses A* with embedding cosine similarity as a heuristic: `f = 0.3 * g_cost + (1 - cosine_sim)`. This guides traversal toward semantically relevant nodes first, pruning irrelevant branches early and shortening the search journey. Falls back to classic spreading activation when A* finds nothing.

## Clean Architecture layout
`core/` has the domain logic (memory, retrieval math, RL), `infrastructure/` has FalkorDB drivers and LLM clients, `interfaces/` has the CLI. Swap the DB without touching core code.

## Hybrid search (BM25 + vector)
Pure vector search misses exact keyword matches (IDs, codes, specific names). Running BM25 fulltext in parallel with cosine vector search covers both cases.

## Super-label strategy for fulltext
FalkorDB doesn't support multi-label fulltext indexes (`Entity|Concept`). All Entity and Concept nodes get an additional `:Searchable` label, and the fulltext index is built on `:Searchable(name)`. This is the FalkorDB-idiomatic approach.

## Application-managed UUIDs
FalkorDB's internal `id()` returns integers that can be reused after node deletion. All nodes carry a `uid` property (UUID4) for reliable, permanent identification. This decouples business logic from DB internals.

## Config via env vars
No hardcoded model names or API keys in source. Everything reads from `.env` so you can hot-swap models or endpoints without code changes.

## PyTorch RL on Apple Silicon
Librarian policy is a small MLP (768 -> 128 -> 4). Trained locally via REINFORCE on MPS. The state encoder (BAAI/bge-base-en-v1.5) runs on CPU to avoid MPS memory allocation issues in tight loops.

## Soft-delete everywhere
Nodes are never hard-deleted. `is_active = false` makes them invisible to retrieval but preserves history. When an Event node is deactivated, its `:FOLLOWS` chain gets bridged around it.

## Memory immutability
The Librarian can update metadata (confidence, heat, access counts) but factual properties (`name`, `summary`, `content`) are blocked at the RL environment level. This prevents destructive updates during autonomous curation.

## Session-based multi-tenancy
All nodes carry a `session_id`. Composite uniqueness (enforced via `MERGE` on `name + session_id`) and query-level pre-filtering ensure isolation between concurrent agent sessions sharing the same FalkorDB instance.
