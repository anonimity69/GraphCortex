"""
LLM-as-a-Judge Reward Pipeline.
Grants RL rewards based on how well the main Research Agent answered
a user's query after the Librarian Agent mutated the Graph context.
"""
from google import genai
import re
import logging
from graph_cortex.config.llm import GEMINI_API_KEY, LLM_MODEL, LLM_TEMPERATURE, LLM_MAX_TOKENS

class LLMRewardJudge:
    def __init__(self):
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.model = LLM_MODEL
        
        self.eval_prompt = (
            "You are an impartial Judge evaluating AI answers.\n"
            "You will be given a [Question], a [Ground Truth], and an [Agent Answer].\n"
            "Score the Agent Answer against the Ground Truth on a scale from 0.0 to 1.0.\n"
            "0.0 = completely incorrect or hallucinations.\n"
            "1.0 = perfect match in meaning (exact phrasing not required).\n\n"
            "You MUST output exactly one number at the very end of your response inside brackets, like: [0.85]\n\n"
        )

    def evaluate_answer(self, question: str, ground_truth: str, agent_answer: str) -> float:
        """
        Calls the LLM to grade the Agent's answer.
        """
        full_prompt = (
            f"{self.eval_prompt}"
            f"[Question]: {question}\n"
            f"[Ground Truth]: {ground_truth}\n"
            f"[Agent Answer]: {agent_answer}\n"
        )
        
        try:
            from google.genai import types
            response = self.client.models.generate_content(
                model=self.model,
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    temperature=LLM_TEMPERATURE,
                    max_output_tokens=LLM_MAX_TOKENS
                )
            )
            
            # Extract score from brackets [X.XX] using regex
            match = re.search(r'\[([0-9]*\.?[0-9]+)\]', response.text)
            if match:
                score = float(match.group(1))
                # Clamp score
                return max(0.0, min(1.0, score))
            else:
                logging.warning(f"[Judge Warning] Could not find bracketed score. LLM Output: {response.text}")
                return 0.0
                
        except Exception as e:
            logging.error(f"[Judge Error] API call failed: {str(e)}")
            return 0.0
