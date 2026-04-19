# Module 17: RL Memory Curation (Production Librarian)

## Files Covered
- `src/graph_cortex/core/rl/action_env.py`
- `src/graph_cortex/core/rl/reward_judge.py`
- `src/graph_cortex/core/agents/librarian.py`
- `src/graph_cortex/core/rl/policy.py`
- `src/graph_cortex/core/agents/librarian.py`
- `src/graph_cortex/core/rl/policy.py`

---

## What This Layer Does

Instead of manual rule-coding (e.g., "delete nodes older than 30 days"), we use **Reinforcement Learning** to discover the most efficient graph topologies. We deploy a **Production Librarian Agent** that is rewarded for mutating the graph in ways that improve the **Research Agent's** accuracy on real-world reasoning benchmarks.

### From Simulation to Backend Optimization
While early development focused on a "Forward-Pass Skeleton," the current system utilizes a **Localized PyTorch Policy Network**:
1.  **Hardware Acceleration**: The policy runs natively on Apple Silicon via **MPS (Metal Performance Shaders)**.
2.  **Backpropagation**: The system performs real-time gradient descent via the **REINFORCE** algorithm.
3.  **Autonomous Swarm**: The Librarian is a persistent background actor in the CLI, performing maintenance cycles without user interaction.

---

## The RL Environment (`action_env.py`)

The `GraphMemoryEnv` translates discrete tokens from an LLM policy into physical state changes in Neo4j.

```python
class GraphMemoryEnv(gym.Env):
    def __init__(self):
        super(GraphMemoryEnv, self).__init__()
        self.curation = MemoryCuration()
        
        # 0: NOOP, 1: ADD, 2: UPDATE, 3: SOFT-DELETE
        self.action_space = spaces.Discrete(4)
```

### The Production Integration
The `LibrarianAgent` loads its trained weights from `librarian_policy_weights.pt` on boot. It uses `SentenceTransformer` to encode graph context into 768-D tensors before passing them to the policy network.

### The Step Function
The `step()` function is the heart of the environment. It receives an action and its parameters (kwargs) and executes it via the `MemoryCuration` service.

| Action | Mapping | Description |
| :--- | :--- | :--- |
| **0 (NOOP)** | No Action | The Librarian decides the current graph context is already optimal. |
| **1 (ADD)** | `merge_node` | Injects a new entity or concept into the graph to bridge a reasoning gap. |
| **2 (UPDATE)** | `update_node` | Modifies relationship weights or metadata on existing nodes. |
| **3 (DELETE)** | `set_node_active_status` | Flags a node as `is_active=False` (Soft-Delete) to prune noise. |

---

## The Reward Loop: LLM-as-a-Judge (`reward_judge.py`)

Deep Reinforcement Learning requires a high-fidelity reward signal. We use **Gemini 2.0 Flash** as an impartial referee to grade the performance of the system *after* the Librarian has modified the graph.

### The Evaluation Flow
1.  **Observation**: The environment presents a question and the current graph neighborhood.
2.  **Action**: The Librarian makes a mutation (e.g., soft-deleting a noisy "hub" node).
3.  **Inference**: The Research Agent attempts to answer the question using the *new* graph topology.
4.  **Judging**: The `LLMRewardJudge` compares the Agent's answer against the **Ground Truth** from the HotpotQA dataset.
5.  **Scoring**: Gemini returns a score from `0.0` (failure) to `1.0` (perfect), which is fed back into the RL policy as a reward.

```python
def evaluate_answer(self, question, ground_truth, agent_answer):
    # Prompting Gemini to assign a score inside brackets [0.95]
    ...
    match = re.search(r'\[([0-9]*\.?[0-9]+)\]', response.text)
    return float(match.group(1))
```

---

---

## The Auto-Sanitization Heuristic

Beyond its neural policy, the Librarian Agent implements a high-priority **Sanitization Phase** to keep the graph "Logic-Dense":

1.  **Pattern Match**: The agent scans for `Message` nodes containing error artifacts (e.g., "Rate limits or quotas exceeded").
2.  **Pruning**: It automatically flags these nodes as `is_active: false`.
3.  **Result**: This prevents the Research Agent from retrieving broken API responses during the Spreading Activation phase, ensuring context windows are reserved for pure factual knowledge.

## Why This Matters
By integrating the Librarian as a production-ready PyTorch actor rather than a static script, GraphCortex achieves **Active Maintenance**. The memory doesn't just grow; it evolves guided by a policy that has been fine-tuned on the full scale of the HotpotQA reasoning dataset.
