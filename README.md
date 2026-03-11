<p align="center">
  <img src="./assets/banner.svg" width="100%" alt="GraphCortex" />
</p>

<h1 align="center">GraphCortex</h1>

<p align="center">
  <strong>The self-healing memory layer for AI agents.</strong><br />
  A knowledge graph that autonomously cleans, merges, and optimizes itself—powered by reinforcement learning.
</p>

<p align="center">
  <a href="./docs/implementation_plan_rl_training.md">RL Training Plan</a> &nbsp;·&nbsp;
  <a href="./src/graph_cortex/interfaces/cli/main.py">CLI</a> &nbsp;·&nbsp;
  <a href="http://localhost:8000/docs">API Docs</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/arch-clean%20architecture-1D9E75?style=flat-square&labelColor=085041" />
  <img src="https://img.shields.io/badge/api-fastapi-7F77DD?style=flat-square&labelColor=3C3489" />
  <img src="https://img.shields.io/badge/db-neo4j-7F77DD?style=flat-square&labelColor=3C3489" />
  <img src="https://img.shields.io/badge/compute-ray%20serve-1D9E75?style=flat-square&labelColor=085041" />
  <img src="https://img.shields.io/badge/search-hybrid%20bm25-7F77DD?style=flat-square&labelColor=3C3489" />
  <img src="https://img.shields.io/badge/rl-grpo%20fine--tuning-1D9E75?style=flat-square&labelColor=085041" />
</p>

---

## The problem with AI agent memory

Most agent memory systems are passive. They store what you put in, return what you ask for, and silently rot over time.

Run any agent long enough and you hit the same three failure modes:

**Graph noise.** Automated extraction is imprecise. You end up with five nodes representing the same concept, contradictory facts weighted equally, and stale context that actively corrupts retrieval. Your context window fills with redundant junk.

**Reasoning staleness.** Information that was useful ten minutes ago can become harmful to a decision being made now. Standard databases don't forget—they accumulate. The longer your agent runs, the worse it reasons.

**Retrieval friction.** Vector search alone misses structural relationships between facts. Static knowledge graphs capture relationships, but they're too rigid to adapt without constant manual maintenance.

The result is a memory system that degrades at exactly the moment your agent needs to be most reliable.

---

## GraphCortex

GraphCortex is a **self-optimizing memory layer** built on Neo4j and orchestrated by a distributed Ray Serve cluster. It combines a multi-agent swarm with a reinforcement learning policy to maintain a knowledge graph that doesn't just store information—it actively restructures itself to reason better over time.

**This is not another RAG wrapper.** Tools like LlamaIndex give you better retrieval *from* a static graph. GraphCortex gives you a graph that gets *structurally better* the more it's used. The difference is whether your memory system is passive infrastructure or an active, learning participant.

---

## How it works

Three specialized agents run concurrently on a Ray Serve cluster:

### Researcher Agent
Handles every query. Uses a Spreading Activation algorithm with Lateral Inhibition to pull tight, relevant context sub-graphs—avoiding the "Hub Explosion" problem where over-connected nodes dominate every result regardless of relevance.

### Summarizer Agent
Runs asynchronously after each conversation turn. Extracts entities and relationships from new interactions and wires them into the Episodic memory timeline without blocking the main thread.

### Librarian Agent *(the core innovation)*
Runs a continuous RL loop in the background. It observes **Graph Heat**—a composite signal built from node access frequency, structural centrality, and retrieval success—and applies three operations:

- **Merge** — collapses duplicate or near-duplicate nodes into canonical representations
- **Prune** — soft-deletes stale, low-signal, or erroneous context (including extraction noise and rate-limit artifacts)
- **Strengthen** — reinforces edges between nodes that consistently co-appear in successful reasoning chains

The policy is trained via GRPO fine-tuning. Better graph usage → stronger reward signal → smarter optimization. It learns what good memory looks like for your specific workload.

### Memory layers

| Layer | What it holds |
|---|---|
| Working Memory | Active conversation context |
| Episodic Memory | Time-stamped events and past interactions |
| Semantic Memory | Distilled, stable world knowledge |

---

## Quickstart

Deploy Neo4j, the Ray cluster, and the full agent swarm in one command. Optimized for Apple Silicon (ARM64).

```bash
# 1. Clone and configure
git clone https://github.com/anonimity69/GraphCortex.git
cd GraphCortex
cp .env.example .env  # Add your LLM API key (Gemini, OpenAI, or OpenRouter)

# 2. Launch the stack
./setup.sh
```

Once running:

| Service | URL |
|---|---|
| REST API | `http://localhost:8000` |
| Swagger UI | `http://localhost:8000/docs` |
| Ray Dashboard | `http://localhost:8265` |
| Neo4j Browser | `http://localhost:7475` |
| Agent REPL | `docker attach graphcortex_swarm` |

---

## REST API

GraphCortex exposes a simple HTTP interface—drop it behind any agent framework.

```bash
curl -X POST "http://localhost:8000/chat" \
     -H "Content-Type: application/json" \
     -d '{"message": "Analyze the latest hardware trends in robotics."}'
```

### See the Librarian in action

```
> User:    "Add a memory about the Voyager 1 mission status."
  System:   Researcher writes node. Summarizer extracts relationships.

  [60s later — background]
  Librarian: Detects a redundant 'Voyager' tag from an earlier extraction.
  Librarian: Merges nodes. Removes a stale rate-limit error artifact.
  Librarian: Graph is tighter. Retrieval is faster.

> User:    /curate
  System:   RL policy runs manually. Mission topology is restructured.
            Confidence scores updated. Two low-heat nodes pruned.
```

The graph is measurably better after this session than before it started.

---

## Use cases

**Long-running autonomous agents** — agents operating over hours or days need memory that doesn't degrade under load. GraphCortex keeps the knowledge base clean as context accumulates.

**Self-healing knowledge bases** — technical documentation, research corpora, or support systems that need to stay accurate without constant manual curation.

**Multi-hop reasoning** — applications requiring complex inference chains across dynamic, frequently-updated datasets where relationship fidelity matters.

---

## Why this matters

Storage is cheap. Attention is expensive.

The limiting factor for the next generation of AI agents isn't compute or model quality—it's memory. How much relevant context can an agent hold? How quickly does its knowledge base degrade? How much human intervention does maintenance require?

GraphCortex is built on the premise that agent memory should be a first-class, self-improving system. One that learns what to forget, what to prioritize, and how to organize itself for whatever reasoning step comes next.

---

## Stack

| Layer | Technology |
|---|---|
| Graph Database | Neo4j |
| Distributed Agents | Ray Serve + Asyncio |
| RL Policy | PyTorch (GRPO fine-tuning) |
| Search | Hybrid BM25 + vector |
| API | FastAPI |
| LLM Routing | Gemini / OpenAI / OpenRouter |

---

<p align="center">
  Built for agents that need to think longer than one conversation.
</p>
