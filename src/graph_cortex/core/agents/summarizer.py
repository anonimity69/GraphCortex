import json
import re
import logging
from graph_cortex.core.agents.base_agent import BaseAgent
from graph_cortex.config.llm import DEFAULT_SUMMARIZER_PROMPT

class SummaryAgent(BaseAgent):
    """
    The Summary Agent observes the conversation turn (User Input + Agent Response)
    and strictly extracts structural Semantic/Episodic triples to feed back into Neo4j.
    """
    def __init__(self):
        # We enforce a strict JSON-mode style prompt for the summarizer
        struct_prompt = (
            f"{DEFAULT_SUMMARIZER_PROMPT}\n\n"
            "You MUST return ONLY a valid JSON object matching this exact schema:\n"
            "{\n"
            '  "summary": "Short 1 sentence description of the interaction",\n'
            '  "entities": [\n'
            '    {"entity": "Name1", "concept": "Category1", "relation": "RELATES_TO"}\n'
            "  ]\n"
            "}\n"
            "Do not include markdown blocks like ```json."
        )
        super().__init__(name="Summarizer", system_prompt=struct_prompt)

    async def extract_and_consolidate(self, user_input: str, agent_response: str) -> dict:
        """
        Queries the LLM for structured extraction of the conversation.
        """
        interaction_text = f"User: {user_input}\nAgent: {agent_response}"
        logging.info(f"[{self.name}] Extracting structural knowledge from interaction...")
        
        llm_response = await self.query_llm(user_input=interaction_text)
        
        raw_text = llm_response.get("response", "{}").strip()
        
        # Clean up accidental markdown blocks if the LLM hallucinated them
        raw_text = re.sub(r"^```json\s*", "", raw_text)
        raw_text = re.sub(r"^```\s*", "", raw_text)
        raw_text = re.sub(r"\s*```$", "", raw_text)
        
        try:
            extracted_data = json.loads(raw_text)
        except json.JSONDecodeError as e:
            logging.error(f"[{self.name}] Failed to parse JSON. Raw LLM Output:\n{raw_text}")
            extracted_data = {"summary": "Extraction Failed.", "entities": []}
            
        logging.info(f"[{self.name}] Extraction complete. Found {len(extracted_data.get('entities', []))} semantic relationships.")
        return extracted_data
