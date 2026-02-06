# Module 17: RL Memory Curation

## Files Covered
- `src/graph_cortex/core/rl/action_env.py`
- `src/graph_cortex/core/rl/reward_judge.py`
- `src/graph_cortex/core/rl/trainer.py`

---

## What These Files Do

These files form the **Intelligence Layer** (Phase 4). They map the domain of Graph Database maintenance into the mathematical domain of deeply recursive Reinforcement Learning.

Instead of writing static Python rules like `If a node hasn't been used in 5 days, delete it`, we use AI. We treat the Graph Database as a "Board Game". We deploy a **Librarian Agent** to play the game by mutating connections. If the Librarian makes the graph better (proven by the Research Agent successfully answering questions faster and more accurately), it gets a High Score (`Reward = +1`). 

We train this via **Group Relative Policy Optimization (GRPO)** using Volcano Engine RL (`VeRL`).

---

## Full Code with Line-by-Line Explanation

### 1. The RL Environment (`action_env.py`)

```python
import gymnasium as gym
from gymnasium import spaces
from graph_cortex.core.memory.curation import MemoryCuration

class GraphMemoryEnv(gym.Env):
    def __init__(self, config: Dict[str, Any] = None):
        super(GraphMemoryEnv, self).__init__()
        self.curation = MemoryCuration()
        self.action_space = spaces.Discrete(4)
```
We subclass `gym.Env`, standardizing the interface so mathematical tooling (like PyTorch / VeRL frameworks) can natively interact with it.
The Librarian can output four discrete actions mathematically bound to `0, 1, 2, 3`.

```python
    def step(self, action: int, action_kwargs: dict):
        if action == 3:  # SOFT-DELETE
            node_id = action_kwargs.get("node_id")
            self.curation.set_node_active_status(node_id=node_id, status=False)
```
When `step` is called by the RL Rollout phase, we execute deterministic Graph manipulations. Here we use the `SOFT-DELETE` mechanism established in Phase 3. 

### 2. The Objective Reward Judge (`reward_judge.py`)

A massive pitfall in RL is "Reward Hacking" — if we reward the Librarian simply for deleting things, it will delete the entire graph to maximize scores. We must reward the *Outcome*.

```python
class LLMRewardJudge:
    def evaluate_answer(self, question: str, ground_truth: str, agent_answer: str) -> float:
        # Prompt: Score the Agent Answer against the Ground Truth from 0.0 to 1.0.
        ...
        match = re.search(r'\[([0-9]*\.?[0-9]+)\]', response.text)
        score = float(match.group(1))
        return max(0.0, min(1.0, score))
```
This is an **LLM-as-a-Judge** pipeline.
Once the Librarian mutates the Graph, we ask the *ResearchAgent* a question. The Researcher retrieves context from the mutated Graph and gives an answer.
The Gemini API acts as a cold, calculating referee, scoring the answer. This is our `Reward`.

### 3. The Skeleton Trainer (`trainer.py`)

```python
class RLSkeletonTrainer:
    def run_local_simulation_loop(self):
        for ep in range(self.episodes):
            
            # 1. Rollout Phase
            state, _ = self.env.reset(...)
            simulated_action = 3 # Librarian decides to flag a node as noisy
            
            # 2. Environment Transition
            next_state, base_reward, done, _, info = self.env.step(...)
            
            # 3. Reward Phase
            score = self.judge.evaluate_answer(...)
            
            # 4. Advantage / Gradient Update
            # weights updated locally.
```
This file is a structural blueprint of a GRPO Rollout. If you ran a real `VeRL` command locally on an Apple Silicon M-Series chip against 8 Billion parameter models, Unified Memory would quickly crash during Backpropagation. 

Therefore, this file is a decoupled simulator representing exactly where the logic binds. To run RL properly, you move this loop to an NVIDIA RunPod instance, pip install VeRL and Ray, and the loop distributes the Forward and Backward passes across multiple compute cards using PyTorch natively.

---

## Conclusion
The GraphCortex ecosystem brings together pure mathematical lateral inhibition, distributed API load balancers, memory sharding techniques, and deep Reinforcement Learning concepts into a single seamless pedagogical pipeline.
