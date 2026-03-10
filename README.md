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
# GraphCortex 🧠

**The self-optimizing, autonomous memory layer for AI agents.**

![GraphCortex Demo](./assets/demo.gif)

[Website](https://graphcortex.ai) | [Documentation](https://docs.graphcortex.ai) | [Discord](https://discord.gg/graphcortex)

---

### 🔥 The self-healing memory grid that improves while you sleep.
GraphCortex is not just another RAG wrapper. It is a distributed, neuro-symbolic memory grid that actively optimizes its own knowledge structure using Reinforcement Learning. While traditional knowledge graphs decay and become noisy, GraphCortex actually gets smarter the more it’s used.

---

### 🧠 The Problem: Knowledge Decay
Most AI agent memory systems (RAG, Vector DBs, Static Knowledge Graphs) suffer from three "agent-killing" problems:
1. **Graph Noise**: Automated extraction creates redundant, fragmented, or conflicting nodes.
2. **Reasoning Staleness**: Information that was relevant 10 minutes ago becomes a bottleneck for current reasoning.
3. **Retrieval Friction**: Vector-only search misses the complex relationships, while standard Graphs are too rigid to adapt.

---

### ⚡ The Solution: Autonomous Intelligence
GraphCortex introduces the **Librarian Swarm**—a fleet of background agents that treat your knowledge graph like a living organism.
* **Self-Optimizing**: Uses a PyTorch-based RL policy to decide which nodes to merge, prune, or strengthen.
* **Heuristic Cleansing**: Automatically identifies and soft-deletes "Rate Limit" errors, system noise, and hallucinations.
* **Distributed & Scalable**: Orchestrated via Ray Serve to handle massive memory loads across multiple LLM backends.

---

### 🤖 How It Works
1. **Researcher Agent**: Interprets user intent and navigates the Graph Topology to find both semantic matches and structural relationships.
2. **Summarizer Agent**: Consolidates new interactions into high-density episodic events, extracting entities and relations in the background.
3. **Librarian Agent (The Brain)**: Runs a continuous RL loop. It observes the "Graph Heat" and applies mutations (ADD, UPDATE, DELETE) to improve the global reasoning score.

---

### 🚀 Quickstart: The "Aha" Moment
Launch the swarm and watch the Librarian optimize your memory in real-time.

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start the Swarm (REPL)
python src/graph_cortex/interfaces/cli/main.py
```

**Try this interaction:**
1. **User >** "Add a memory about the Voyager 1 mission status."
2. **System >** *Researcher saves the node... Summarizer extracts relationships...*
3. **Wait 60s >** *The background Librarian wakes up, identifies a redundant 'Voyager' tag, merges it, and cleans up a stray rate-limit error.*
4. **User >** `/curate` -> *Watch the RL policy manually optimize the mission topology.*

---

### 🎯 Use Cases
* **Long-Term Agent Memory**: Give your agents a memory that doesn't just grow—it evolves.
* **Self-Healing Knowledge Bases**: Maintenance-free KGs for technical documentation or complex research.
* **Reasoning-Heavy Applications**: Systems that require multi-hop inference across dynamic, changing datasets.

---

### 🛠️ The Stack
* **Orchestration**: Ray Serve & Asyncio (High-concurrency agent swarm).
* **Graph Engine**: Neo4j (Neuro-symbolic storage).
* **Intelligence**: PyTorch (Local RL Policy training & inference).
* **Inference**: Gemini / LLM Routing (Provider-agnostic).

---

### 🧩 Why This Matters
Storage is cheap, but **attention is expensive**. The future of AI isn't about storing more data—it's about building systems that know what to forget, what to prioritize, and how to organize themselves for the next reasoning step. GraphCortex is building that nervous system.

---
*Built for the next generation of truly autonomous agents.*

<p align="center">
  <strong>Give your AI a structural brain. It's about time.</strong>
</p>
