# Module 14: Multi-Agent CLI Interface

## File Covered
`src/graph_cortex/interfaces/cli/main.py`

---

## The Interface Ecosystem

GraphCortex is no longer just a database; it is a **Distributed Multi-Agent Swarm**. The CLI serves as the central command-and-control center where the Researcher, Summarizer, and Librarian agents collaborate in real-time.

### The Swarm Architecture

1.  **Researcher Agent**: Navigates the graph to find connected context for your queries.
2.  **Summarizer Agent**: Background worker that compresses conversations into factual nodes.
3.  **Librarian Agent**: Active maintenance agent that optimizes the graph using Reinforcement Learning.

---

## 🚀 System Boot Sequence

When you run `python src/graph_cortex/interfaces/cli/main.py`, the system executes a multi-stage startup:

### 1. Zero-Noise Logging
The system suppresses standard Ray and uvicorn logs, redirecting all architectural events to `Logs/admin_system.log`. This ensures the CLI remains a clean, distraction-free playground.

### 2. Ray Serve & LLM Routing
The CLI initializes a local **Ray cluster** and deploys the `LLMEngineDeployment`. This allows all agents in the swarm to communicate with the central Gemini 2.0 router asynchronously.

### 3. Librarian Weight Loading
During initialization, the Librarian Agent scans the root directory for `librarian_policy_weights.pt`. If found, it automatically loads its trained neural network state, transitioning from random heuristics to active, learned intelligence.

---

## 🛠️ CLI Command Reference

| Command | Category | Description |
| :--- | :--- | :--- |
| `/help` | General | Displays the command menu. |
| `/stats` | Health | Verifies that all agents in the swarm are alive and responding. |
| `/data` | Dashboard| Shows live Neo4j node counts and RL training dataset statistics. |
| `/train` | RL | **Neural Fine-Tuning**. Runs local PyTorch REINFORCE trials on Apple Silicon. |
| `/curate` | Maintenance | **Active Curation**. Manually triggers a maintenance cycle (Sanitization + RL optimization). |
| `/clear` | Memory | Flushes the current Working Memory and starts a fresh session. |
| `/exit` | Shutdown | Gracefully terminates Ray Serve and synchronizes background tasks. |

---

## 🤖 Automatic Background Maintenance

One of the most critical features documented in this file is the **Background Maintenance Loop**.

```python
async def background_librarian_task(librarian_agent):
    while True:
        await asyncio.sleep(60) # Wake up every minute
        librarian_agent.curate(context="Auto-maintenance cycle")
```

Every 60 seconds, the Librarian Agent wakes up and performs a two-stage sweep:
1.  **Auto-Sanitize**: It proactively hunts for "Rate Limit" or "System Error" nodes and flags them as inactive.
2.  **RL Optimization**: It uses its neural policy to mutate the graph topology, ensuring the most important information is always closest to the Research Agent's activation path.

---

## How to Interact with the Swarm

The CLI uses a high-performance `asyncio` loop to ensure you can chat with the Researcher while the Summarizer and Librarian work in the background.

1.  **Ask a Question**: The Researcher triggers **Hybrid Search** (BM25 + Semantic) to find answers.
2.  **Observe Logs**: Open a second terminal and run `tail -f Logs/admin_system.log` to see the agents talking to each other.
3.  **Optimize**: Use `/train` to improve the Librarian's intelligence, or `/curate` to see it clean up your graph in real-time.
