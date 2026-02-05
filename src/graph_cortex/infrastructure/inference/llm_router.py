"""
Ray Serve Deployment for the LLM Inference Engine.

Decouples the LLM from the application logic. Currently wraps the Gemini API,
but can be swapped to a local HuggingFace/vLLM backend without changing
the downstream agent code.
"""

from ray import serve
from google import genai
from graph_cortex.config.llm import GEMINI_API_KEY, LLM_MODEL

@serve.deployment(num_replicas=1, ray_actor_options={"num_cpus": 1})
class LLMEngineDeployment:
    def __init__(self):
        # Initialize the Gemini client
        print(f"[LLM Router] Initializing Gemini Client with model: {LLM_MODEL}")
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.model = LLM_MODEL
        
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
            # Note: For Gemini, we pass the full text block. If using pure structured output,
            # we would pass schema options here, but we will handle JSON instruction in the prompt.
            response = self.client.models.generate_content(
                model=self.model,
                contents=full_prompt
            )
            return {"status": "success", "response": response.text}
            
        except Exception as e:
            print(f"[LLM Router Error] {str(e)}")
            return {"status": "error", "error": str(e)}

# Bind the deployment so it can be served via `serve run`
app = LLMEngineDeployment.bind()
