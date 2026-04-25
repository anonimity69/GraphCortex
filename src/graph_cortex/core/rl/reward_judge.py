from google import genai
from google.genai import types
import re
import logging

from graph_cortex.config.llm import GEMINI_API_KEY, LLM_MODEL, LLM_TEMPERATURE, LLM_MAX_TOKENS


class LLMRewardJudge:
    """Scores agent answers against ground truth. Returns float in [0, 1]."""

    def __init__(self):
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.model = LLM_MODEL

        self.eval_prompt = (
            "You are an impartial Judge evaluating AI answers and memory curation quality.\n"
            "You will be given a [Question], a [Ground Truth], an [Agent Answer], and optionally [Librarian Actions].\n"
            "Score the Agent Answer against the Ground Truth on a scale from 0.0 to 1.0.\n\n"
            "PENALTY RULES:\n"
            "- If [Librarian Actions] show destructive merging (specific entities -> generic concepts), return [0.0].\n"
            "- If [Librarian Actions] attempted to modify immutable properties (name, summary, etc.), return [0.0].\n\n"
            "Otherwise: 0.0 = completely wrong, 1.0 = perfect match in meaning.\n\n"
            "Output exactly one number in brackets at the end, like: [0.85]\n\n"
        )

    def evaluate_answer(self, question: str, ground_truth: str, agent_answer: str, curation_logs: str = "None") -> float:
        prompt = (
            f"{self.eval_prompt}"
            f"[Question]: {question}\n"
            f"[Ground Truth]: {ground_truth}\n"
            f"[Agent Answer]: {agent_answer}\n"
            f"[Librarian Actions]: {curation_logs}\n"
        )

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=LLM_TEMPERATURE,
                    max_output_tokens=LLM_MAX_TOKENS
                )
            )

            match = re.search(r'\[([0-9]*\.?[0-9]+)\]', response.text)
            if match:
                return max(0.0, min(1.0, float(match.group(1))))
            else:
                logging.warning(f"Judge: no bracketed score in response")
                return 0.0

        except Exception as e:
            logging.error(f"Judge API error: {e}")
            return 0.0
