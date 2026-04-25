# Architecture Decisions

## Neo4j over flat vector DBs
Need graph traversals for spreading activation and multi-hop reasoning. Vector DBs can't do that natively. Neo4j gives us topology + vector indexes in the same store.

## Clean Architecture layout
`core/` has the domain logic (memory, retrieval math, RL), `infrastructure/` has Neo4j drivers and LLM clients, `interfaces/` has the CLI. Swap the DB without touching core code.

## Hybrid search (BM25 + vector)
Pure vector search misses exact keyword matches (IDs, codes, specific names). Running BM25 fulltext in parallel with cosine vector search covers both cases.

## Config via env vars
No hardcoded model names or API keys in source. Everything reads from `.env` so you can hot-swap models or endpoints without code changes.

## PyTorch RL on Apple Silicon
Librarian policy is a small MLP (768 -> 128 -> 4). Trained locally via REINFORCE on MPS. The state encoder (BAAI/bge-base-en-v1.5) runs on CPU to avoid MPS memory allocation issues in tight loops.

## Soft-delete everywhere
Nodes are never hard-deleted. `is_active = false` makes them invisible to retrieval but preserves history. When an Event node is deactivated, its `:FOLLOWS` chain gets bridged around it.

## Memory immutability
The Librarian can update metadata (confidence, heat, access counts) but factual properties (`name`, `summary`, `content`) are blocked at the RL environment level. This prevents destructive updates during autonomous curation.

## Session-based multi-tenancy
All nodes carry a `session_id`. Composite uniqueness constraints (`name + session_id`) and in-index pre-filtering ensure isolation between concurrent agent sessions sharing the same Neo4j instance.
