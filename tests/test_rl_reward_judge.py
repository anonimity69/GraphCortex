import unittest
from graph_cortex.core.rl.reward_judge import LLMRewardJudge


class TestRewardJudge(unittest.TestCase):
    def setUp(self):
        self.judge = LLMRewardJudge()

    def test_correct_answer_scores_high(self):
        score = self.judge.evaluate_answer(
            "What pattern separates domain from infrastructure logic?",
            "Clean Architecture",
            "The pattern is Clean Architecture, decoupling DB logic from core algorithms."
        )
        self.assertGreaterEqual(score, 0.8)

    def test_hallucination_scores_low(self):
        score = self.judge.evaluate_answer(
            "What pattern separates domain from infrastructure logic?",
            "Clean Architecture",
            "The agent uses quantum tunneling to extract memories."
        )
        self.assertLessEqual(score, 0.2)


if __name__ == "__main__":
    unittest.main()
