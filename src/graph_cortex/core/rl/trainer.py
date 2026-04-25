import json
import os
import time

import torch
import torch.optim as optim
from torch.distributions.categorical import Categorical
from sentence_transformers import SentenceTransformer

from graph_cortex.core.rl.action_env import GraphMemoryEnv
from graph_cortex.core.rl.reward_judge import LLMRewardJudge
from graph_cortex.core.rl.policy import LibrarianPolicy


class RLPyTorchTrainer:
    def __init__(self, use_gpu: bool = True, dataset_path: str = "data/rl_training/hotpot_qa_sample.jsonl"):
        self.env = GraphMemoryEnv()
        self.judge = LLMRewardJudge()
        self.dataset_path = dataset_path

        self.device = torch.device("mps" if torch.backends.mps.is_available() and use_gpu else "cpu")
        print(f"[RL] device={self.device}")

        self.policy = LibrarianPolicy().to(self.device)
        self.optimizer = optim.Adam(self.policy.parameters(), lr=0.001)

        # BAAI encoder on CPU — MPS has memory allocation issues in tight loops
        self.state_encoder = SentenceTransformer(
            'BAAI/bge-base-en-v1.5',
            device=str(self.device).replace('mps', 'cpu')
        )

    def run_training_loop(self, episodes: int = 500):
        if not os.path.exists(self.dataset_path):
            print(f"[RL] Dataset missing: {self.dataset_path}")
            return

        samples = []
        with open(self.dataset_path, "r") as f:
            for line in f:
                samples.append(json.loads(line))
                if episodes and len(samples) >= episodes:
                    break

        print(f"[RL] Starting training, {len(samples)} episodes")

        for ep, sample in enumerate(samples):
            state_text, _ = self.env.reset(options={"subgraph_context": f"Question: {sample['question']}"})

            state_vector = self.state_encoder.encode(state_text)
            state_tensor = torch.FloatTensor(state_vector).to(self.device).unsqueeze(0)

            action_probs = self.policy(state_tensor)
            m = Categorical(action_probs)
            action_tensor = m.sample()
            action = action_tensor.item()
            log_prob = m.log_prob(action_tensor)

            # map neural action to env kwargs
            kwargs = {}
            if action == 1:
                kwargs = {"name": f"Hotpot_Entity_{ep}", "label": "Concept"}
            elif action == 2:
                kwargs = {"node_id": "mock_update_id", "properties": {"confidence": 0.99}}
            elif action == 3:
                kwargs = {"node_id": "mock_delete_id"}

            next_state, _, _, _, info = self.env.step(action, kwargs)
            probs_str = ', '.join(f'{p:.2f}' for p in action_probs[0].tolist())
            print(f"  ep={ep+1} action={info['action_taken']} probs=[{probs_str}] -> {info['status']}")

            # reward: LLM-as-judge
            # NOTE: feeding ground truth as agent_answer here — this is a bootstrap,
            # not a real closed-loop eval. Good enough for initial policy shaping.
            ground_truth = sample['answer']
            agent_answer = f"The knowledge graph returns: {ground_truth}"

            curation_logs = (
                f"Action: {info.get('action_taken')} | "
                f"Status: {info.get('status')} | "
                f"Violation: {info.get('action_violation', 'None')}"
            )
            score = self.judge.evaluate_answer(sample['question'], ground_truth, agent_answer, curation_logs=curation_logs)

            # REINFORCE update
            loss = -log_prob * torch.tensor([score]).to(self.device)
            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()

            if ep > 0 and ep % 50 == 0:
                torch.save(self.policy.state_dict(), "librarian_policy_weights.pt")
                print(f"  [checkpoint] saved at ep {ep}")

        print(f"[RL] Training done. {len(samples)} episodes.")


if __name__ == "__main__":
    trainer = RLPyTorchTrainer()
    trainer.run_training_loop(episodes=500)
