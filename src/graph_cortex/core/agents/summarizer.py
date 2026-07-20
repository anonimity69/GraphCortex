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
            "CRITICAL: Be extremely detailed. If the user mentions locations (e.g. 'in a box', 'bedroom'), "
            "objects (e.g. 'keys'), or specific details, extract ALL of them as SEPARATE entities and connect them with relations. "
            "Do NOT bury important nouns inside the 'properties' dictionary. Every important object, person, or location MUST be its own distinct entity. "
            "Preserve literal string values. No markdown blocks.\n\n"
            "EXAMPLE INPUT:\n"
            "User: I stored my keys in the blue box in the garage.\n"
            "EXAMPLE OUTPUT:\n"
            "{\n"
            '  "summary": "User stored keys in a blue box in the garage.",\n'
            '  "entities": [\n'
            '    {"entity": "keys", "concept": "Object", "relation": "STORED_IN", "properties": {}},\n'
            '    {"entity": "blue box", "concept": "Container", "relation": "LOCATED_IN", "properties": {}},\n'
            '    {"entity": "garage", "concept": "Location", "relation": "CONTAINS", "properties": {}}\n'
            '  ]\n'
            "}\n"
        )
        super().__init__(name="Summarizer", system_prompt=prompt)

    def _repair_json(self, json_str: str) -> str:
        in_string = False
        escape = False
        for char in json_str:
            if escape:
                escape = False
            elif char == '\\':
                escape = True
            elif char == '"':
                in_string = not in_string
                
        repaired = json_str
        if in_string:
            repaired += '"'
            
        stack = []
        for char in repaired:
            if char in '{[':
                stack.append(char)
            elif char in '}]':
                if stack:
                    stack.pop()
                    
        while stack:
            char = stack.pop()
            if char == '{':
                repaired += '}'
            elif char == '[':
                repaired += ']'
                
        return repaired

    async def extract_and_consolidate(self, user_input: str, agent_response: str) -> dict:
        interaction_text = f"User: {user_input}\nAgent: {agent_response}"
        logging.info("[Summarizer] Extracting entities...")

        llm_response = await self.query_llm(user_input=interaction_text)

        raw_text = (llm_response.get("response") or "{}").strip()

        # use regex to find the json block, ignoring conversational text
        json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            # quick fix for trailing commas in arrays/objects
            json_str = re.sub(r',\s*([\]}])', r'\1', json_str)
            try:
                data = json.loads(json_str)
            except json.JSONDecodeError as e:
                logging.warning(f"[Summarizer] Bad JSON from LLM: {e}. Attempting auto-repair...")
                try:
                    repaired_str = self._repair_json(json_str)
                    data = json.loads(repaired_str)
                    logging.info(f"[Summarizer] Auto-repair successful!")
                except json.JSONDecodeError as e2:
                    logging.error(f"[Summarizer] Auto-repair failed: {e2} - {repaired_str[:200]}")
                    data = {"summary": "Extraction failed.", "entities": []}
        else:
            logging.error(f"[Summarizer] No JSON found in LLM response: {raw_text[:200]}")
            data = {"summary": "Extraction failed.", "entities": []}

        logging.info(f"[Summarizer] Got {len(data.get('entities', []))} entities")
        return data
