"""
Base Agent class for the Multi-Agent swarm.
Provides shared utilities for querying Neo4j and direct LLM interaction.
"""

import logging
from graph_cortex.infrastructure.inference.llm_client import LLMClient

class BaseAgent:
    def __init__(self, name: str, system_prompt: str):
        self.name = name
        self.system_prompt = system_prompt
        # Initialize direct LLM client
        self.llm = LLMClient()
            
    async def query_llm(self, user_input: str, context: str = "") -> dict:
        """
        Sends a request to the direct LLM client.
        """
        try:
            return await self.llm.query(
                system_prompt=self.system_prompt,
                user_input=user_input,
                context=context
            )
        except Exception as e:
            logging.error(f"[{self.name}] LLM Query failed: {e}")
            return {"status": "error", "error": str(e)}
