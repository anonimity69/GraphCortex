"""
Standalone LLM Inference Client.
Wraps the Google GenAI SDK for direct use by agents without Ray Serve.
"""

from google import genai
import logging
import asyncio
from google.genai import types
from graph_cortex.config.llm import (
    GEMINI_API_KEY, 
    LLM_MODEL, 
    LLM_TEMPERATURE, 
    LLM_MAX_TOKENS
)

class LLMClient:
    def __init__(self, api_key: str = None, model: str = None):
        target_key = api_key or GEMINI_API_KEY
        target_model = model or LLM_MODEL
        
        if not target_key:
            logging.error("[LLM Client] GEMINI_API_KEY is missing. LLM calls will fail.")
            
        logging.info(f"[LLM Client] Initializing direct LLM Client with model: {target_model}")
        self.client = genai.Client(api_key=target_key)
        self.model = target_model

    async def query(self, system_prompt: str, user_input: str, context: str = "") -> dict:
        """
        Performs a direct call to the Gemini API.
        """
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
            error_msg = "API Timeout: The model took too long to generate a response (90s limit)."
            logging.error(f"[LLM Client Error] {error_msg}")
            return {"status": "error", "error": error_msg}
        except Exception as e:
            logging.error(f"[LLM Client Error] {str(e)}")
            return {"status": "error", "error": str(e)}
