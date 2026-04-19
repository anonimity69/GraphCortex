# Module 17: RL Memory Curation (The Intelligence Layer)

## Files Covered
- `src/graph_cortex/core/rl/action_env.py`
- `src/graph_cortex/core/rl/reward_judge.py`

---

## What This Layer Does

The **Intelligence Layer** (Phase 4) is where GraphCortex transitions from a passive database to an active, self-optimizing "brain." 

Instead of manual rule-coding (e.g., "delete nodes older than 30 days"), we use **Reinforcement Learning** to discover the most efficient graph topologies. We deploy a **Librarian Agent** that is rewarded for mutating the graph in ways that improve the **Research Agent's** accuracy on real-world reasoning benchmarks.

### The "Forward-Pass Simulator"
To avoid the massive compute requirements of local backward-pass training, Phase 4 is implemented as a **Highly Advanced Forward-Pass Simulator**. This allows us to:
1.  Verify the bridge between LLM actions and Neo4j transactions.
2.  Test the LLM-as-a-Judge reward pipeline.
3.  Simulate rollout loops locally before porting to a cloud GPU for official training.

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

## Why This Matters
By building this "Gymnasium" bridge first, we ensure that when we eventually port to a multi-GPU cluster (using **VeRL** and **GRPO**), the "muscles" (Neo4j curation) and "logic" (prompting/scoring) are already hardened and verified.
