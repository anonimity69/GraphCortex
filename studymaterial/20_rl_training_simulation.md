# Module 20: Neural Policy Training (The Brain)

## File Covered
- `src/graph_cortex/core/rl/trainer.py`
- `src/graph_cortex/core/rl/policy.py`

---

## From Simulation to Reality

Module 20 covers the **Neural Policy Training** phase, where GraphCortex transitions from validating logic to actually learning behaviors. We've moved beyond the "Skeleton Trainer" and implemented a production-grade **PyTorch Reinforcement Learning** pipeline.

---

## The Neural Architecture (`policy.py`)

The `LibrarianPolicy` is a Multi-Layer Perceptron (MLP) that acts as the "decision engine" for graph curation.

- **Input Layer**: 768-dimensional vector (Semantic embedding of the current graph context).
- **Hidden Layers**: Two 128-node ReLU layers with Dropout (0.1) for regularization.
- **Output Layer**: 4-dimensional Softmax (Probabilities for NOOP, ADD, UPDATE, SOFT-DELETE).

### Hardware Acceleration (MPS)
To enable high-speed training on local hardware, the trainer utilizes **Apple Silicon MPS (Metal Performance Shaders)**. This allows the system to perform backpropagation on the M4 GPU, making neural fine-tuning feasible on a laptop.

---

## The Learning Algorithm: REINFORCE

We utilize the **REINFORCE (Policy Gradient)** algorithm to update the Librarian's weights based on performance.

### The Training Loop
The `RLPyTorchTrainer` executes a genuine deep learning lifecycle for each sample:

```python
for ep in range(episodes):
    # 1. Forward Pass: Get action probabilities from the MLP
    action_probs = self.policy(state_tensor)
    m = Categorical(action_probs)
    action = m.sample()
    
    # 2. Execution: perform the graph mutation in Neo4j
    next_state, reward, done, _ = self.env.step(action.item())
    
    # 3. Loss Calculation: -log_prob * reward
    # Rewards come from the LLM-as-a-Judge Reward Pipeline
    loss = -m.log_prob(action) * reward
    
    # 4. Backpropagation: Update neural weights via Optimizer
    self.optimizer.zero_grad()
    loss.backward()
    self.optimizer.step()
```

---

## Production Weight Management

The trainer periodically serializes the learned weights into a persistent file: `librarian_policy_weights.pt`.

1.  **Checkpointing**: Every 50 episodes, the model state is saved.
2.  **Hot-Swapping**: The live `LibrarianAgent` in the CLI is designed to detect and load this `.pt` file on startup. This creates a seamless "Train -> Deploy" loop where the agent's intelligence grows over time.

---

## How to Start a Training Run
To initiate a localized deep learning session, use the specialized CLI command:
```bash
/train
```
This triggers the `RLPyTorchTrainer` to run a trial batch (e.g., 3 episodes) using the HotpotQA dataset, updating the local neural policy based on live LLM feedback.
