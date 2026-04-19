# Module 20: RL Training Simulation (The Brain)

## File Covered
- `src/graph_cortex/core/rl/trainer.py`

---

## Moving from Static to Dynamic

Module 20 covers the **RL Training Simulation**, which acts as the "connective tissue" that brings the Environment, the Judge, and the Data together. 

In Phase 4, we don't just run queries; we run **episodes**. An episode is a single trial where the AI tries something, sees the result, and learns from the reward.

---

## The Simulation Architecture

The `RLSkeletonTrainer` is designed as a **Policy Simulation**. It simulates a high-end Reinforcement Learning algorithm called **GRPO (Group Relative Policy Optimization)**.

### Why GRPO?
GRPO is a modern RL algorithm (used in models like DeepSeek-R1) that calculates rewards relative to a group of outcomes rather than a fixed baseline. This makes it incredibly effective for task-oriented agents like the Graph Librarian.

### The Trainer Loop
The `run_training_loop()` function executes a structured lifecycle for every sample in the dataset:

```python
for ep, sample in enumerate(samples):
    # 1. Reset: Load a new HotpotQA question into the environment
    state, _ = self.env.reset(options={"subgraph_context": sample['question']})
    
    # 2. Rollout: Simulate the Librarian's decision
    # (ADD, UPDATE, or SOFT-DELETE)
    next_state, _, _, _, info = self.env.step(simulated_action, kwargs)
    
    # 3. Reward: Ask the LLM Judge to grade the resulting graph quality
    score = self.judge.evaluate_answer(sample['question'], ground_truth, agent_answer)
    
    # 4. Learning: Simulated Backpropagation
    # In a real cluster, this is where PyTorch updates the model weights.
    # In our simulator, we log the reward for verification.
```

---

## Local Simulation vs. Cloud Training

One of the most important concepts in Module 20 is the separation of **Logic** and **Compute**.

| local Simulator (Mac/M3) | Cloud Trainer (NVIDIA H100) |
| :--- | :--- |
| **Logic Verification**: Tests if the Gym environment works. | **Policy Learning**: Performs trillions of floating-point ops. |
| **Forward Pass**: Calculates rewards and states. | **Backward Pass**: Calculates gradients and updates weights. |
| **Skeleton Code**: `trainer.py` handles the orchestration. | **VeRL Framework**: `trainer.py` logic is ported to the cluster. |

### The "Skeleton" Design
The reason we call it a "Skeleton" trainer is that it contains 100% of the **integration logic** but 0% of the **computational overhead**. This allows you to verify that your whole Phase 4 system is "ready for lift-off" without needing a $40,000 GPU server.

---

## How to Run a Training Trial
To see the "Brain" in action, run the CLI and use the training command:
```bash
/train
```
This will trigger the `RLSkeletonTrainer` to run 3 sample episodes through your local Neo4j instance, proving that your Librarian Agent is ready for official fine-tuning.
