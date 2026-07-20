<p align="center">
  <img src="./assets/banner.svg" width="100%" alt="GraphCortex" />
</p>

<p align="center">
  A self-optimizing knowledge graph memory layer for AI agents, built on FalkorDB.
</p>

<p align="center">
  <a href="./docs/implementation_plan_rl_training.md">RL Training Plan</a> &nbsp;·&nbsp;
  <a href="./src/graph_cortex/interfaces/cli/main.py">CLI</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/db-falkordb-FF6B35?style=flat-square&labelColor=CC4400" />
  <img src="https://img.shields.io/badge/search-hybrid%20bm25%20%2B%20A*-7F77DD?style=flat-square&labelColor=3C3489" />
  <img src="https://img.shields.io/badge/rl-grpo-1D9E75?style=flat-square&labelColor=085041" />
</p>

<p align="center">
  <img src="./assets/demo.gif" width="100%" alt="GraphCortex Demo" />
</p>

---

## What this does

Most agent memory is passive — store what goes in, return what's asked for, degrade silently over time. Run any agent long enough and you hit three problems: duplicate/contradictory nodes from automated extraction, stale context that corrupts retrieval, and vector search that misses structural relationships.

GraphCortex is a memory layer that doesn't just store information — it restructures itself. Three agents run concurrently:

- **Researcher** — handles queries using A*-guided graph traversal with lateral inhibition. Uses embedding similarity as a heuristic to find the most relevant nodes faster, then reconstructs edges between anchor nodes via `shortestPath`.
- **Summarizer** — runs async after each turn. Extracts entities/relationships from conversations and wires them into the episodic timeline.
- **Librarian** — the interesting one. Runs an RL policy loop (PyTorch, REINFORCE) that observes graph state and decides whether to add bridging nodes, bump confidence on weak nodes, or soft-delete stale ones. Trained on HotpotQA via an LLM-as-judge reward signal.

The Librarian enforces memory immutability — it can update metadata (confidence, heat, access counts) but core factual properties (`name`, `summary`, etc.) are blocked at the environment level.

### Memory layers

| Layer | What it holds |
|---|---|
| Working Memory | Active conversation context |
| Episodic Memory | Time-stamped event chain (`:FOLLOWS` linked) |
| Semantic Memory | Entities, concepts, relationships |

---

## Architecture

```mermaid
graph TD
    User([User]) <--> CLI[Swarm CLI]
    
    subgraph Swarm[GraphCortex Swarm]
        Researcher[Researcher]
        Summarizer[Summarizer]
        Librarian[Librarian]
    end
    
    CLI <--> Researcher
    Researcher --> RetrievalEngine[Retrieval Engine]
    RetrievalEngine --> AStar[A* Traversal]
    RetrievalEngine --> Inhibition[Lateral Inhibition]
    
    CLI --> Summarizer
    Summarizer --> Ingestion[Memory Ingestion]
    
    Librarian --> RL[RL Policy]
    RL --> GraphOps[Merge / Prune / Strengthen]
    
    subgraph Infra[Infrastructure]
        FalkorDB[(FalkorDB)]
        LLM[LLM API]
    end
    
    RetrievalEngine <--> FalkorDB
    Ingestion --> FalkorDB
    GraphOps --> FalkorDB
    Researcher <--> LLM
    Summarizer <--> LLM
    Librarian <--> LLM
```

```mermaid
sequenceDiagram
    participant U as User
    participant C as CLI
    participant R as Researcher
    participant S as Summarizer
    participant L as Librarian
    participant DB as FalkorDB

    U->>C: Query
    C->>R: Process
    R->>DB: Hybrid Search (BM25 + Vector)
    DB-->>R: Anchor Nodes
    R->>DB: A* Traversal (embedding heuristic)
    DB-->>R: Context Sub-graph
    R->>R: Lateral Inhibition
    R->>C: Answer
    C-->>U: Response

    C->>S: Turn Data
    S->>S: Extract Entities
    S->>DB: Update Episodic Memory

    loop Background
        L->>DB: Read Graph State
        L->>L: Policy Inference
        L->>DB: Curate (Add/Update/Delete)
    end
```

---

## Quickstart

Deploys FalkorDB + the Swarm CLI. Works on Mac (Intel/Apple Silicon), Linux, and Windows (WSL2).

```bash
git clone https://github.com/anonimity69/GraphCortex.git
cd GraphCortex
cp .env.example .env  # add your GEMINI_API_KEY
chmod +x setup.sh shutdown.sh
./setup.sh
```

| Action | Command |
|---|---|
| Start | `./setup.sh` |
| Stop | `./shutdown.sh` |
| Graph Browser | [localhost:3000](http://localhost:3000) |

The setup script handles port conflicts, waits for the DB to stabilize, and drops you into the CLI.

---

## CLI Commands

```
/data     - graph + dataset stats
/train    - run RL training (HotpotQA)
/curate   - trigger librarian manually
/monitor  - librarian metrics
/clear    - new session
/exit     - shutdown
```

---

## Stack

| Layer | Tech |
|---|---|
| Graph DB | FalkorDB (GraphBLAS engine) |
| Agents | Asyncio |
| RL | PyTorch (REINFORCE) |
| Search | Hybrid BM25 + Cosine Vector + A* |
| LLM | Gemini / OpenAI / OpenRouter |

---

<p align="center">
  Built for agents that need to think longer than one conversation.
</p>
