import json
import re
import logging
from graph_cortex.core.agents.base_agent import BaseAgent
from graph_cortex.config.llm import DEFAULT_SUMMARIZER_PROMPT


class SummaryAgent(BaseAgent):
    def __init__(self):
        prompt = (
            f"{DEFAULT_SUMMARIZER_PROMPT}\n\n"
            "You MUST return ONLY a valid JSON object matching this exact schema:\n"
            "{\n"
            '  "summary": "Short 1 sentence description of the interaction",\n'
            '  "entities": [\n'
            '    {\n'
            '      "entity": "Name1", \n'
            '      "concept": "Category1", \n'
            '      "relation": "RELATES_TO",\n'
            '      "properties": {"key": "literal_value"}\n'
            '    }\n'
            "  ]\n"
            "}\n\n"
            "If the text mentions specific attributes or codes, include them in 'properties'. "
            "Preserve literal string values. No markdown blocks."
        )
        super().__init__(name="Summarizer", system_prompt=prompt)

    async def extract_and_consolidate(self, user_input: str, agent_response: str) -> dict:
        interaction_text = f"User: {user_input}\nAgent: {agent_response}"
        logging.info("[Summarizer] Extracting entities...")

        llm_response = await self.query_llm(user_input=interaction_text)

        raw_text = llm_response.get("response", "{}").strip()

        # strip markdown fences if the LLM hallucinated them
        raw_text = re.sub(r"^```json\s*", "", raw_text)
        raw_text = re.sub(r"^```\s*", "", raw_text)
        raw_text = re.sub(r"\s*```$", "", raw_text)

        try:
            data = json.loads(raw_text)
        except json.JSONDecodeError:
            logging.error(f"[Summarizer] Bad JSON from LLM: {raw_text[:200]}")
            data = {"summary": "Extraction failed.", "entities": []}

        logging.info(f"[Summarizer] Got {len(data.get('entities', []))} entities")
        return data
