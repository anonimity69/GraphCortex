import logging
from graph_cortex.infrastructure.inference.llm_client import LLMClient


class BaseAgent:
    def __init__(self, name: str, system_prompt: str):
        self.name = name
        self.system_prompt = system_prompt
        self.llm = LLMClient()

    async def query_llm(self, user_input: str, context: str = "") -> dict:
        try:
            return await self.llm.query(
                system_prompt=self.system_prompt,
                user_input=user_input,
                context=context
            )
        except Exception as e:
            logging.error(f"[{self.name}] LLM query failed: {e}")
            return {"status": "error", "error": str(e)}
