# Module 19: RL Dataset Preparation (The Fuel)

## File Covered
- `scripts/prepare_rl_dataset.py`

---

## Why We Need a Dataset

Reinforcement Learning is data-hungry. To train the **Librarian Agent**, we need a benchmark that tests the **Research Agent's** ability to perform complex reasoning. 

If the Librarian modifies the graph, we need to know if that modification made it easier or harder to find the right answer.

---

## HotpotQA: The Gold Standard for Graphs

GraphCortex uses the full **HotpotQA** dataset for its RL training cycles. 

### What is HotpotQA?
HotpotQA is a multi-hop question-answering dataset. Unlike standard SQuAD-style datasets where the answer is in a single paragraph, HotpotQA requires the AI to:
1.  Find Fact A.
2.  Use Fact A to find Fact B.
3.  Synthesize Fact A and Fact B into a single answer.

**Why this is perfect for GraphCortex:**  
Multi-hop reasoning is exactly what a Knowledge Graph is designed for. If the Librarian effectively curates the connections between "Fact A" and "Fact B," the Spreading Activation algorithm will find the answer faster and with less noise.

---

## The Scaffolding Script

The `prepare_rl_dataset.py` script automates the retrieval of this "fuel."

```python
from datasets import load_dataset

def prepare_dataset():
    # Load the full training split from HotpotQA
    dataset = load_dataset("hotpot_qa", "distractor", split="train")
    subset = dataset # Pull the entire split for production training
    
    # Export to JSONL (JSON Lines) for efficient line-by-line reading
    file_path = "data/rl_training/hotpot_qa_sample.jsonl"
    with open(file_path, "w", encoding="utf-8") as f:
        for item in subset:
            clean_item = {
                "question": item["question"],
                "answer": item["answer"],
                "supporting_facts": item["supporting_facts"]
            }
            f.write(json.dumps(clean_item) + "\n")
```

### Script Features
1.  **HuggingFace Integration**: Uses the standard `datasets` library to pull from the cloud.
2.  **JSONL Format**: Stores data in JSON Lines format, which allows the `RLSkeletonTrainer` to stream memory-efficiently without loading the entire 100MB+ dataset into RAM.
3.  **Bootstrap Ready**: This script provides the "Ground Truth" that the **Reward Judge** uses to grade the agents.

---

## How to Run
To prepare the fuel for your training sessions, run:
```bash
python scripts/prepare_rl_dataset.py
```
This creates the `data/rl_training/` directory and populates it with the full scale of reasoning samples needed for neural policy optimization.
