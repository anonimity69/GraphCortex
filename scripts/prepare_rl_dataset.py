#!/usr/bin/env python3
"""
Downloads a subset of the HotpotQA dataset from HuggingFace
to bootstrap the RL-Driven Memory Curation training loop.

HotpotQA is ideal because it requires multi-hop reasoning, 
testing the Research Agent's ability to navigate the Neo4j Graph.
"""

from datasets import load_dataset
import json
import os

def prepare_dataset():
    print("[Dataset Prep] Loading HotpotQA from HuggingFace...")
    # Load the validation split to keep the size small for local testing
    dataset = load_dataset("hotpot_qa", "distractor", split="validation")
    
    # We will sample 100 questions for our local RL Proof-of-Concept
    subset = dataset.select(range(100))
    
    output_dir = "data/rl_training"
    os.makedirs(output_dir, exist_ok=True)
    
    file_path = os.path.join(output_dir, "hotpot_qa_sample.jsonl")
    print(f"[Dataset Prep] Exporting 100 samples to {file_path}...")
    
    with open(file_path, "w", encoding="utf-8") as f:
        for item in subset:
            clean_item = {
                "question": item["question"],
                "answer": item["answer"],
                "supporting_facts": [{"title": t, "sent_id": s} for t, s in zip(item["supporting_facts"]["title"], item["supporting_facts"]["sent_id"])]
            }
            f.write(json.dumps(clean_item) + "\n")
            
    print(f"[Dataset Prep] Complete! The RL Trainer can now read from '{file_path}'.")

if __name__ == "__main__":
    prepare_dataset()
