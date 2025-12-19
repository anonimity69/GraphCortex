# GraphCortex
A highly scalable, distributed neuro-symbolic graph memory system for AI agents, featuring spreading activation retrieval and autonomous RL-driven memory curation via GRPO.

## 🚀 Recent Updates & Progress

*   **Virtual Environment Setup**: A dedicated Python virtual environment (`.venv`) has been established.
*   **Architecture Restructuring**: The project has been restructured into an industry-standard, domain-driven architecture to ensure modularity, scalability, and maintainability. The codebase is organized into layers:
    *   `src/`: Core application logic (including the Multi-Layer Memory Framework: Working, Episodic, Semantic memory).
    *   `config/`: Configuration and environment management.
    *   `deployments/`: Infrastructure configurations (e.g., Docker setup for Neo4j).
    *   `docs/`: Documentation and system design.
    *   `scripts/`: Operational utilities.
    *   `tests/`: Verification and automated test suites.
*   **Implementation Plan Established**: A detailed two-phase roadmap (`implementation_plan.md`) has been mapped out. Phase 1 focuses on the underlying Storage Substrate (Neo4j integration and MLMF components), and Phase 2 details the dynamic, brain-inspired Spreading Activation Retrieval Engine.

## 🧠 Project Overview

The Distributed Neuro-Symbolic Memory Grid (NS-DMG) aims to evolve AI memory systems beyond flat vector databases. It provides structural, chronological, and semantic context by leveraging Neo4j as the Graph Database layer, combined with spreading activation retrieval techniques to avoid the "Hub Explosion" problem.
