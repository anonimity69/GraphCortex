# GraphCortex — Complete Study Guide

## How to Use This Study Material

This guide is designed to give you total mastery over every line of code in GraphCortex. Read each module in order. By the end, you will be able to explain the entire system to any client, interviewer, or technical stakeholder with full confidence.

---

## Table of Contents

| # | Module | File | Phase |
|---|---|---|---|
| 01 | [Project Architecture & Why It Exists](./01_architecture.md) | — | Overview |
| 02 | [Docker & Environment Configuration](./02_docker_and_env.md) | `docker-compose.yml`, `.env` | Phase 1 |
| 03 | [Neo4j Connection (Singleton Pattern)](./03_neo4j_connection.md) | `neo4j_connection.py` | Phase 1 |
| 04 | [Schema Migrations & Vector Indexes](./04_schema_migrations.md) | `schema_migrations.py` | Phase 1 + 3 |
| 05 | [Working Memory](./05_working_memory.md) | `working.py` | Phase 1 |
| 06 | [Episodic Memory](./06_episodic_memory.md) | `episodic.py` | Phase 1 |
| 07 | [Semantic Memory & Embeddings](./07_semantic_memory.md) | `semantic.py` | Phase 1 + 3 |
| 08 | [Memory Manager Orchestrator](./08_memory_manager.md) | `manager.py` | Phase 1 |
| 09 | [Property Sharding](./09_property_sharding.md) | `sharding.py` | Phase 1 |
| 10 | [Retrieval Queries (Cypher)](./10_retrieval_queries.md) | `retrieval_queries.py` | Phase 2 + 3 |
| 11 | [Lateral Inhibition (The Math)](./11_lateral_inhibition.md) | `inhibition.py` | Phase 2 |
| 12 | [Retrieval Engine (The Brain)](./12_retrieval_engine.md) | `engine.py` | Phase 2 + 3 |
| 13 | [Logger Configuration](./13_logger.md) | `logger.py` | Phase 3 |
| 14 | [CLI Entry Point](./14_cli_main.md) | `main.py` | All |
| 15 | [End-to-End Data Flow Walkthrough](./15_data_flow.md) | — | All |

---

## The One-Paragraph Elevator Pitch

> GraphCortex is a neuro-symbolic memory and context layer for AI agents. Unlike flat vector databases (Pinecone, Qdrant) that retrieve isolated chunks, GraphCortex stores knowledge in a multi-layered Neo4j Knowledge Graph — tracking real-time conversations (Working Memory), compressing them into chronological events (Episodic Memory), and extracting structured facts (Semantic Memory). When the AI needs to recall information, a brain-inspired Spreading Activation algorithm fans outward from anchor nodes, mathematically bounded by Lateral Inhibition to prevent generic "hub" concepts from flooding the context window. The system uses a hybrid Lexical + Semantic Vector dual-trigger to find anchors, meaning it understands meaning (synonyms), not just exact strings.

---

## The Folder Structure (Clean Architecture)

```
GraphCortex/
├── src/graph_cortex/
│   ├── core/                          ← THE BRAIN (Pure logic, zero DB deps)
│   │   ├── memory/
│   │   │   ├── working.py             ← Real-time conversation buffer
│   │   │   ├── episodic.py            ← Chronological event chains
│   │   │   ├── semantic.py            ← Entity/Concept extraction + embeddings
│   │   │   └── manager.py             ← Orchestrator API
│   │   └── retrieval/
│   │       ├── engine.py              ← Spreading Activation controller
│   │       └── inhibition.py          ← Energy decay math
│   │
│   ├── infrastructure/                ← THE TOOLS (DB-specific, swappable)
│   │   ├── db/
│   │   │   ├── neo4j_connection.py    ← Singleton driver
│   │   │   ├── schema_migrations.py   ← Constraints + Vector indexes
│   │   │   └── queries/
│   │   │       └── retrieval_queries.py ← Raw Cypher queries
│   │   └── storage/
│   │       └── sharding.py            ← Property offloading abstraction
│   │
│   ├── interfaces/                    ← THE DELIVERY (Entry points)
│   │   └── cli/
│   │       └── main.py                ← CLI demo & verification
│   │
│   └── config/
│       └── logger.py                  ← Retrieval event logging
│
├── docker-compose.yml                 ← Neo4j container definition
├── .env                               ← Connection credentials
├── pyproject.toml                     ← Project metadata & deps
├── DECISIONS.md                       ← Architectural decision records
└── Logs/                              ← Timestamped retrieval logs
```

### Why This Structure Matters

If a client asks: *"What if we want to switch from Neo4j to AWS Neptune?"*

Your answer: *"We only modify the `infrastructure/` folder. The `core/` contains pure mathematical logic with zero database imports. The retrieval math, memory orchestration, and energy decay formulas remain entirely untouched."*

This is the **Dependency Inversion Principle** — high-level modules (core) do not depend on low-level modules (infrastructure). Both depend on abstractions.
