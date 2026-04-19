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

## 3. Hybrid Search (Phase 5 Evolution)

### The Limits of Pure Vector Search
During extensive benchmarking, we identified "Context Collapse" and "Temporal Blindness." Pure dense vector search excels at retrieving semantically related broader concepts but often fails at "Needle in the Haystack" retrieval—such as finding isolated alphanumeric ID codes or specific chemical names.

### The Hybrid Solution
To solve this, we migrated the Dual-Trigger Retrieval Engine to a fully **Hybrid Search Architecture**:
- Sub-graph triggers now rely on both a **Dense Vector Semantic Index** and a **BM25 Lexical Fulltext Index** executing concurrently. 
- The system naturally balances broad associative reasoning (Vector) with absolute probabilistic keyword precision (BM25 Lucene parsing), granting the LLM total recall over sparsely connected episodic memories without relying on parameter hallucination.

## 4. Configuration-Driven Architecture & Deterministic Scaling

### Eliminating Framework Lock-In
We purged all hardcoded legacy strings (e.g., specific Gemini model names) from the core logic. GraphCortex now enforces strict dependency injection via configuration files (`.env`), rendering the `LLMEngineDeployment` router fully architecture-agnostic. You can hot-swap from an OpenAI endpoint to a local VLLM deployment pulling an open model (like Gemma 4 31B) strictly through environmental variables. Let the platform adapt to the compute, not the other way around.

### Deterministic Feedback Loops for RL
We established a strict `TEMPERATURE=0.0` ceiling and heavily sanitized string injection pipelines (e.g., stripping Cypher injection risks within the `SummarizerAgent`). The Reward Pipeline strictly demands repeatable extraction formatting, allowing the RL policy gradients to accurately score outputs without the unpredictable noise synonymous with generative creativity.
## 5. Localized PyTorch RL & Apple Silicon Optimization (Phase 6)

### The Move from Skeleton to Simulation
Originally, Phase 4 was implemented as a "Skeleton" simulator of logic. To bridge the gap to true intelligence, we migrated the curation policy to a genuine **PyTorch Deep Reinforcement Learning** architecture.

### The Hardware Choice
To ensure the system remains hardware-agnostic yet incredibly fast on high-end consumer laptops, we opted for **Metal Performance Shaders (MPS)** acceleration. 
- The `LibrarianPolicy` is a Multi-Layer Perceptron (MLP) mapping 768-dimensional textual embeddings (state) to discrete graph mutations (actions).
- By using the **REINFORCE (Policy Gradient)** algorithm, the system performs localized backpropagation directly on the Apple Silicon M4 GPU, allowing the AI to "learn" the optimal graph topology for a specific user's logic without needing complex cloud-GPU hyper-scaling during the prototyping phase.

## 6. Multi-Agent Swarm Logic & Production Integration (Phase 7)

### Productionizing the Model
We decoupled the RL model's architecture into a shared `policy.py` module. This allows the system to load trained PyTorch weight serialize files (`.pt`) directly into the **Librarian Agent** during CLI initialization. 

### Swarm Awareness
We expanded the agent swarm from two (Researcher/Summarizer) to three. The **Librarian Agent** is now a fully productive member of the swarm, equipped with the knowledge extracted from 90,000+ HotpotQA training samples. It serves as the bridge between raw, generative summarization and structured, retrieved logical truth.

## 7. Automatic Graph Sanitization & Maintenance Loops (Phase 8)

### Identifying Context Noise
During deployment testing, we discovered that "API Rate Limit" and "System Error" messages were inadvertently being stored as memory nodes. These artifacts create "Semantic Noise," leading to retrieval degradation as the agents attempt to reason over error logs instead of factual data.

### Background "Gardening"
We implemented an asynchronous **Background Maintenance Task** in the CLI. 
- Every 60 seconds, the Librarian Agent performs a **Sanitization Sweep**, using a Cypher-based heuristic to hunt down and soft-delete error-related nodes.
- This ensures the Graph remains "logic-dense," providing the Research Agent with a clean sub-graph context window while preserving the graph's history via the Global Soft-Delete architecture.
