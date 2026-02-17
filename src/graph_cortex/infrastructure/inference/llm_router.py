"""
Ray Serve Deployment for the LLM Inference Engine.

Decouples the LLM from the application logic. Currently wraps the Gemini API,
but can be swapped to a local HuggingFace/vLLM backend without changing
the downstream agent code.
"""

from ray import serve
from google import genai
import logging
from graph_cortex.config.llm import GEMINI_API_KEY, LLM_MODEL, LLM_TEMPERATURE, LLM_MAX_TOKENS

@serve.deployment(num_replicas=1, ray_actor_options={"num_cpus": 1})
class LLMEngineDeployment:
    def __init__(self, api_key: str = None, model: str = None):
        # Use dynamic injection for API key and model to bypass Ray worker caching
        from graph_cortex.config.llm import GEMINI_API_KEY, LLM_MODEL
        
        target_key = api_key or GEMINI_API_KEY
        target_model = model or LLM_MODEL
        
        logging.info(f"[LLM Router] Initializing LLM Client with model: {target_model}")
        self.client = genai.Client(api_key=target_key)
        self.model = target_model
        
    async def __call__(self, request: dict) -> dict:
        """
        Accepts a dictionary payload containing the prompts.
        Expected keys: system_prompt, user_input, context (optional)
        """
        system_prompt = request.get("system_prompt", "")
        user_input = request.get("user_input", "")
        context = request.get("context", "")
        
        # Build the final prompt payload
        if context:
            full_prompt = f"System: {system_prompt}\n\nContext Memory:\n{context}\n\nUser: {user_input}"
        else:
            full_prompt = f"System: {system_prompt}\n\nUser: {user_input}"
            
        try:
            import asyncio
            from google.genai import types
            coro = self.client.aio.models.generate_content(
                model=self.model,
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    temperature=LLM_TEMPERATURE,
                    max_output_tokens=LLM_MAX_TOKENS
                )
            )
            
            # Bound the request to 12 seconds so that tenancity retry loops on 429 errors 
            # don't lock the UI forever.
            response = await asyncio.wait_for(coro, timeout=12.0)
            return {"status": "success", "response": response.text}
            
        except asyncio.TimeoutError:
            error_msg = "API Timeout: Rate limits or quotas exceeded. Please check your model provider limits."
            logging.error(f"[LLM Router Error] {error_msg}")
            return {"status": "error", "error": error_msg}
        except Exception as e:
            logging.error(f"[LLM Router Error] {str(e)}")
            return {"status": "error", "error": str(e)}

# Bind the deployment so it can be served via `serve run`
app = LLMEngineDeployment.bind()
