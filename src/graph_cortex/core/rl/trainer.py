import json
import os
from graph_cortex.core.rl.action_env import GraphMemoryEnv
from graph_cortex.core.rl.reward_judge import LLMRewardJudge
import time

class RLSkeletonTrainer:
    def __init__(self, use_gpu: bool = False, dataset_path: str = "data/rl_training/hotpot_qa_sample.jsonl"):
        self.env = GraphMemoryEnv()
        self.judge = LLMRewardJudge()
        self.use_gpu = use_gpu
        self.dataset_path = dataset_path

    def run_training_loop(self, episodes: int = 5):
        """
        Iterates through actual dataset samples and simulates the RL Loop.
        """
        if not os.path.exists(self.dataset_path):
            print(f"[RL Trainer Error] Dataset not found at {self.dataset_path}. Please run 'python scripts/prepare_rl_dataset.py' first.")
            return

        print(f"[RL Trainer] Starting Local Learning Loop (Max Episodes: {episodes})")
        
        samples = []
        with open(self.dataset_path, "r") as f:
            for line in f:
                samples.append(json.loads(line))
                if len(samples) >= episodes:
                    break

        for ep, sample in enumerate(samples):
            print(f"\n--- Learning Episode {ep+1}/{len(samples)} ---")
            print(f"[Sample] Question: {sample['question'][:60]}...")
            
            # 1. Rollout Phase
            state, _ = self.env.reset(options={"subgraph_context": f"Question: {sample['question']}"})
            
            # 2. Environment Transition (Varying Actions to verify full suite)
            # Ep 0: ADD, Ep 1: UPDATE, Ep 2+: SOFT-DELETE
            if ep == 0:
                simulated_action = 1 # ADD
                kwargs = {"name": "Optimized_Node", "label": "Entity", "properties": {"reasoning": "multi-hop"}}
            elif ep == 1:
                simulated_action = 2 # UPDATE
                kwargs = {"node_id": "mock_update_id", "properties": {"status": "trained"}}
            else:
                simulated_action = 3 # SOFT-DELETE
                kwargs = {"node_id": "mock_delete_id"}
            
            next_state, _, _, _, info = self.env.step(simulated_action, kwargs)
            print(f"[Policy] Librarian Action: {info['action_taken']}")
            print(f"[Environment] Result: {info['status']}")
            
            # 3. Reward Phase (LLM-as-a-Judge)
            # The judge compares the Agent's answer (simulated here) against the Ground Truth
            ground_truth = sample['answer']
            agent_answer = f"According to the graph, {ground_truth}" # Mocking a correct-ish answer
            
            score = self.judge.evaluate_answer(sample['question'], ground_truth, agent_answer)
            print(f"[Reward Judge] Accuracy Score: {score}")
            
            # 4. Simulated PPO Update
            print(f"[Optimizer] Backpropagating reward {score} into local policy weights...")
            time.sleep(1)

        print("\n[RL Trainer] Training Session Complete.")

if __name__ == "__main__":
    trainer = RLSkeletonTrainer()
    trainer.run_training_loop(episodes=2)
