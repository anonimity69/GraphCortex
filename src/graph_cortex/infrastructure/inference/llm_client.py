from google import genai
from google.genai import types
import logging
import asyncio

from graph_cortex.config.llm import (
    GEMINI_API_KEY,
    LLM_MODEL,
    LLM_TEMPERATURE,
    LLM_MAX_TOKENS
)


class LLMClient:
    def __init__(self, api_key: str = None, model: str = None):
        key = api_key or GEMINI_API_KEY
        self.model = model or LLM_MODEL

        if not key:
            logging.error("GEMINI_API_KEY missing — LLM calls will fail")

        self.client = genai.Client(api_key=key)

    async def query(self, system_prompt: str, user_input: str, context: str = "") -> dict:
        if context:
            full_prompt = f"System: {system_prompt}\n\nContext Memory:\n{context}\n\nUser: {user_input}"
        else:
            full_prompt = f"System: {system_prompt}\n\nUser: {user_input}"

        try:
            coro = self.client.aio.models.generate_content(
                model=self.model,
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    temperature=LLM_TEMPERATURE,
                    max_output_tokens=LLM_MAX_TOKENS
                )
            )

            response = await asyncio.wait_for(coro, timeout=90.0)
            return {"status": "success", "response": response.text}

        except asyncio.TimeoutError:
            logging.error("LLM timeout (90s)")
            return {"status": "error", "error": "LLM request timed out (90s limit)"}
        except Exception as e:
            logging.error(f"LLM error: {e}")
            return {"status": "error", "error": str(e)}
