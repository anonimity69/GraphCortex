# Architectural Decisions

This document outlines the core architectural and technical decisions made during the development of GraphCortex (NS-DMG), demonstrating the engineering philosophy behind the system.

## 1. Neo4j vs. Flat Vector Databases (Pinecone, Milvus, Qdrant)

### The Limitation of Flat Vectors
Vector databases are standard practice for Retrieval-Augmented Generation (RAG) because they excel at nearest-neighbor similarity searches. However, they are fundamentally "flat". When building long-term memory for advanced AI agents relying on episodic reasoning or logical deduction, vector databases suffer from:
- **Lack of topological context:** They cannot natively construct associative networks (how Concept A relates to Concept B) without calculating heavy, manual intersections on the application layer.
- **Lost chronology:** Storing conversation logs in a vector space strips away the strict chronological sequence of events (Episodic reasoning).

### The Neo4j Solution
We chose Neo4j because intelligent, neuro-symbolic memory requires **topology**. 
- **Graph Traversal (Spreading Activation):** By using a graph, the AI can trigger an anchor node and mathematically "traverse" outward to find connected concepts, natively simulating the human brain's associative memory.
- **Multi-Layered Memory Framework (MLMF):** Neo4j allows us to store short-term interactions (Working Memory), summarize them into chronological chains (`:FOLLOWS` relationships for Episodic Memory), and extract persistent facts (`:RELATED_TO` for Semantic Memory) within the exact same interconnected database.

## 2. Decoupling via Clean Architecture

### The Problem with Prototyping
When building AI applications, developers often mix database queries (like Cypher), LLM API calls, and core logic into single, monolithic scripts. This approach leads to rigid, un-testable, and un-scalable "spaghetti code" that is incredibly difficult to maintain.

### The Clean Architecture Approach
We implemented an industry-standard Domain-Driven Design (Clean Architecture) to ensure maximum modularity and scalability.

- **`core/` (The Brain):** Contains the pure mathematical theory of memory (e.g., Working Memory logic, Lateral Inhibition math, Energy Decay equations). This layer is entirely agnostic—it knows absolutely nothing about Neo4j, Docker, or APIs.
- **`infrastructure/` (The Tools):** Contains the physical database drivers and complex Cypher queries. By isolating this, if we ever need to migrate from local Neo4j to enterprise AWS Neptune, we only modify this single folder. The `core` remains untouched.
- **`interfaces/` (The Delivery):** Contains the entry points where the outside world interacts with the system (like the CLI or future REST APIs).

This strict separation of concerns allows us to write isolated, lightning-fast unit tests for our Energy Decay algorithms without needing to spin up or mock a live database connection, proving the system is engineered for enterprise-grade scalability.
