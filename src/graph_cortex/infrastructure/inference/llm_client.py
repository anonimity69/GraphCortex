from google import genai
from google.genai import types
import logging
import asyncio
import re

from graph_cortex.config.llm import (
    GEMINI_API_KEY,
    LLM_MODEL,
    LLM_TEMPERATURE,
    LLM_MAX_TOKENS
)

MAX_RETRIES = 3


def _parse_retry_delay(error_str: str, default: float = 25.0) -> float:
    """Extract the suggested retry delay from a rate-limit error message."""
    match = re.search(r'retry in ([\d.]+)s', error_str, re.IGNORECASE)
    if match:
        return min(float(match.group(1)) + 1, 60.0)  # +1s buffer, cap at 60s
    return default


class LLMClient:
    def __init__(self, api_key: str = None, model: str = None):
        key = api_key or GEMINI_API_KEY
        self.model = model or LLM_MODEL

        if not key:
            logging.error("GEMINI_API_KEY missing — LLM calls will fail")

        self.client = genai.Client(api_key=key)

    async def query(self, system_prompt: str, user_input: str, context: str = "", response_mime_type: str = "text/plain") -> dict:
        if context:
            full_prompt = f"System: {system_prompt}\n\nContext Memory:\n{context}\n\nUser: {user_input}"
        else:
            full_prompt = f"System: {system_prompt}\n\nUser: {user_input}"

        for attempt in range(MAX_RETRIES + 1):
            try:
                coro = self.client.aio.models.generate_content(
                    model=self.model,
                    contents=full_prompt,
                    config=types.GenerateContentConfig(
                        temperature=LLM_TEMPERATURE,
                        max_output_tokens=LLM_MAX_TOKENS,
                        response_mime_type=response_mime_type,
                        safety_settings=[
                            types.SafetySetting(
                                category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                                threshold=types.HarmBlockThreshold.BLOCK_NONE,
                            ),
                            types.SafetySetting(
                                category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                                threshold=types.HarmBlockThreshold.BLOCK_NONE,
                            ),
                            types.SafetySetting(
                                category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                                threshold=types.HarmBlockThreshold.BLOCK_NONE,
                            ),
                            types.SafetySetting(
                                category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                                threshold=types.HarmBlockThreshold.BLOCK_NONE,
                            ),
                        ]
                    )
                )

                response = await asyncio.wait_for(coro, timeout=180.0)
                return {"status": "success", "response": response.text}

            except asyncio.TimeoutError:
                logging.error("LLM timeout (180s)")
                return {"status": "error", "error": "LLM request timed out (180s limit)"}
            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    delay = _parse_retry_delay(error_str)
                    if attempt < MAX_RETRIES:
                        logging.warning(
                            f"Rate limited (attempt {attempt + 1}/{MAX_RETRIES}). "
                            f"Retrying in {delay:.0f}s..."
                        )
                        await asyncio.sleep(delay)
                        continue
                    logging.error(f"Rate limit persisted after {MAX_RETRIES} retries")
                    return {
                        "status": "error",
                        "error": "Rate limited — please wait a moment and try again."
                    }
                logging.error(f"LLM error: {e}")
                return {"status": "error", "error": str(e)}
