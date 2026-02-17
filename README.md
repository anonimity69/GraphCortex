<p align="center">
  <img src="./assets/banner.svg" width="100%" alt="GraphCortex logo" />
</p>

<p align="center">
  <strong>Distributed neuro-symbolic graph memory for AI agents</strong>
</p>

<p align="center">
  <a href="./docs/implementation_plan_rl_training.md">RL Training Plan</a> &nbsp;·&nbsp;
  <a href="./DECISIONS.md">Architecture Decisions</a> &nbsp;·&nbsp;
  <a href="./src/graph_cortex/interfaces/cli/main.py">Interactive CLI</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/arch-clean%20architecture-1D9E75?style=flat-square&labelColor=085041" />
  <img src="https://img.shields.io/badge/db-neo4j-7F77DD?style=flat-square&labelColor=3C3489" />
  <img src="https://img.shields.io/badge/compute-ray%20serve-1D9E75?style=flat-square&labelColor=085041" />
  <img src="https://img.shields.io/badge/search-hybrid%20bm25-7F77DD?style=flat-square&labelColor=3C3489" />
  <img src="https://img.shields.io/badge/rl-grpo%20fine--tuning-1D9E75?style=flat-square&labelColor=085041" />
</p>

---

GraphCortex is a neuro-symbolic memory and context layer for advanced AI agents. It solves the limitations of flat vector databases by combining a **Multi-Agent Swarm** with a **Neo4j Knowledge Graph** and **Reinforcement Learning (RL)** optimization.

It automatically extracts structural facts, tracks chronological interaction histories, and uses **Spreading Activation** to retrieve deeply connected sub-graphs—now optimized by an RL-driven "Librarian" that curates the graph for maximum logic density.

| | |
|---|---|
| 🧠 **Working Memory** | Real-time short-term buffer for active interactions. |
| 📅 **Episodic Memory** | Sequential event summaries compressed for long-term recall. |
| 🕸️ **Semantic Memory** | Global entity-level abstractions and factual relationships. |
| 🔍 **Hybrid Retrieval** | **(Phase 5)** Parallel BM25 Fulltext + Dense Vector semantic triggers for absolute precision. |
| ⚡ **Spreading Activation** | Neighbors-of-neighbors retrieval bounded by mathematical Lateral Inhibition. |
| ⚖️ **RL Librarian** | Phase 4 Fine-Tuning loop that rewards the agent for higher reasoning accuracy. |
| 🔐 **Deterministic LLM** | Configuration-driven, timeout-resistant routing (Supports Gemma 4 31B Open Models). |

---

## 🏛️ Architecture: Distributed Swarm

GraphCortex runs on a strictly decoupled, multi-agent architecture powered by **Ray Serve**:

*   **Researcher Agent**: Navigates graph topology and executes hybrid retrieval.
*   **Summarizer Agent**: Background actor that extracts knowledge without blocking the user.
*   **Librarian Agent (RL)**: Self-optimizing curation policy that prunes redundant nodes.
*   **Reward Judge**: LLM-as-a-Judge pipeline that grades agent answers against ground truth.

---

## 🚀 Getting Started

GraphCortex is fully executable locally on Mac/Linux with Neo4j.

### Installation
1.  **Clone & Environment**:
    ```bash
    pip install -r requirements.txt
    cp .env.example .env # Add your GEMINI_API_KEY and NEO4J credentials
    ```
2.  **Dataset Prep** (For Phase 4 Training):
    ```bash
    python scripts/prepare_rl_dataset.py # Downloads 100 HotpotQA samples
    ```
3.  **Start the Swarm**:
    ```bash
    python src/graph_cortex/interfaces/cli/main.py
    ```

### Interactive CLI Commands
*   `/help` - Show all available commands.
*   `/data` - Live dashboard of Neo4j node counts and RL dataset status.
*   `/train` - **Live RL Session**. Fine-tunes the Librarian policy using local data.
*   `/clear` - Flush working memory.
*   `/exit` - Graceful shutdown with background task synchronization.

---

## 🎯 Why GraphCortex?

**Standard RAG is flat.** Vector databases retrieve isolated chunks but lose the "topology" of your problem. GraphCortex uses **Persistent Neo4j Topology** and **Active Learning** to ensure your AI understands that "User A belongs_to StartUp Y", and can deduce multi-hop structural logic without hallucinations.

Read the full technical breakdown: **[DECISIONS.md](./DECISIONS.md)**

---

<p align="center">
  <strong>Give your AI a structural brain. It's about time.</strong>
</p>
