import unittest
from graph_cortex.core.rl.reward_judge import LLMRewardJudge

class TestRLRewardJudge(unittest.TestCase):
    def setUp(self):
        self.judge = LLMRewardJudge()
        
    def test_perfect_match(self):
        # A perfectly answering reasoning trace should score near 1.0
        question = "What architectural pattern separates the domain logic from the infrastructure logic?"
        ground_truth = "Clean Architecture"
        agent_answer = "The pattern is known as Clean Architecture, which completely decouples the neo4j database logic from the core GraphCortex memory algorithms."
        
        score = self.judge.evaluate_answer(question, ground_truth, agent_answer)
        print(f"Perfect Match Score: {score}")
        self.assertGreaterEqual(score, 0.8)
        self.assertLessEqual(score, 1.0)
        
    def test_complete_hallucination(self):
        # A wildly incorrect or hallucinated answer should score near 0.0
        question = "What architectural pattern separates the domain logic from the infrastructure logic?"
        ground_truth = "Clean Architecture"
        agent_answer = "The agent uses quantum tunneling to extract memories from the local database."
        
        score = self.judge.evaluate_answer(question, ground_truth, agent_answer)
        print(f"Hallucination Score: {score}")
        self.assertLessEqual(score, 0.2)
        self.assertGreaterEqual(score, 0.0)

if __name__ == "__main__":
    unittest.main()
