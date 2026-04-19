"""
Base Agent class for the Multi-Agent swarm.
Provides shared utilities for querying Neo4j and communicating with the Ray Serve LLM router.
"""

from ray import serve
import ray

class BaseAgent:
    def __init__(self, name: str, system_prompt: str):
        self.name = name
        self.system_prompt = system_prompt
        # Connect to the local Ray cluster if not already connected
        if not ray.is_initialized():
            ray.init(ignore_reinit_error=True)
            
    async def query_llm(self, user_input: str, context: str = "") -> dict:
        """
        Sends a request to the deployed LLM Engine via Ray Serve handles.
        """
        try:
            # Get a handle to the deployment
            handle = serve.get_deployment("LLMEngineDeployment").get_handle()
            
            # Fire an asynchronous RPC
            response_ref = await handle.remote({
                "system_prompt": self.system_prompt,
                "user_input": user_input,
                "context": context
            })
            return response_ref
        except Exception as e:
            return {"status": "error", "error": str(e)}
