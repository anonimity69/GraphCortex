# Phase 4 Implementation Plan: RL-Driven Memory Curation

This document outlines the architecture for **Phase 4: The Intelligence Layer**, adapting the original NS-DMG blueprint for local simulated execution and deployment-ready cloud scaling using Reinforcement Learning.

## Proposed Architecture

### 1. The Action Space & RL Environment
We constrain the Librarian Agents to perform systematic, targeted operations. Large Language Models output text, but our `Gymnasium` environment parses those into discrete mathematical graph manipulation operations.

#### `src/graph_cortex/core/rl/action_env.py`
- Implements `GraphMemoryEnv`, exposing standard `reset` and `step` functions.
- **Strict Operations:** 
  - `ADD`: Inject missing nodes to the graph.
  - `UPDATE`: Tune weights on graph relationships.
  - `SOFT-DELETE`: Invoke `set_node_active_status` to disable toxic/noisy hubs without destroying chronological integrity.
  - `NOOP`: Take no action if the graph is properly distilled.

---

### 2. The Objective Reward Loop (LLM-as-a-Judge)
The RL policy needs gradients to learn, but manual scoring is impossible. We establish an impartial Judge simulation.

#### `src/graph_cortex/core/rl/reward_judge.py`
- Exposes `LLMRewardJudge`, binding natively to `gemini-2.0-flash`.
- **The Evaluation Loop**:
  1. The Librarian modifies the Neo4j context.
  2. The Retriever executes Spreading Activation on the new context.
  3. The Research Agent answers a benchmark question.
  4. The Gemini Judge assigns a decimal score (`0.0 - 1.0`) against the Ground Truth.
- Built-in mathematical safety testing in `tests/test_rl_reward_judge.py`.

---

### 3. VeRL & GRPO Training Simulator
Running full Volcano Engine Reinforcement Learning backwards passes locally on Apple Silicon can rapidly overflow Unified Memory constraints.

#### `src/graph_cortex/core/rl/trainer.py`
- Provides the simulation of a Group Relative Policy Optimization (GRPO) epoch.
- Defines exactly where the Ray Cluster integration injects the rollout experiences.
- Scales flawlessly for NVIDIA / CUDA deployment later.

---

### 4. Automated Data Scaffolding
RL loops require large scale benchmark data.
#### `scripts/prepare_rl_dataset.py`
- Automatically integrates HuggingFace `datasets`.
- Downloads validation subsets of the `HotpotQA` reasoning dataset straight to `data/rl_training/hotpot_qa_sample.jsonl`.
