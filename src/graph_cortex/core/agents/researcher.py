import logging
from graph_cortex.core.agents.base_agent import BaseAgent
from graph_cortex.core.retrieval.engine import RetrievalEngine
from graph_cortex.config.llm import DEFAULT_RESEARCHER_PROMPT


class ResearchAgent(BaseAgent):
    """Queries the memory graph, formats context, gets an LLM answer."""

    def __init__(self):
        super().__init__(name="Researcher", system_prompt=DEFAULT_RESEARCHER_PROMPT)
        self.retrieval_engine = RetrievalEngine()

    async def process_query(self, user_query: str, session_id: str) -> dict:
        logging.info(f"[Researcher] query='{user_query}' session={session_id}")

        retrieval_results = self.retrieval_engine.retrieve([user_query], session_id=session_id)

        context_string = ""
        if retrieval_results["status"] == "Hit":
            nodes = retrieval_results["network"]
            edges = retrieval_results.get("edges", [])

            context_string = "Retrieved Knowledge Graph Context:\n"
            context_string += "### Entities & Concepts:\n"
            for node in nodes:
                context_string += f"- ({node['type']}) {node['name']} [Distance: {node['distance']}]\n"

            context_string += "\n### Relationships:\n"
            for edge in edges:
                context_string += f"- ({edge['source_name']}) -[{edge['rel_type']}]-> ({edge['target_name']})\n"

            logging.info(f"[Researcher] {len(nodes)} nodes, {len(edges)} edges")
        else:
            logging.info("[Researcher] No context found, going zero-shot")

        llm_response = await self.query_llm(user_input=user_query, context=context_string)

        if llm_response.get("status") == "error":
            final_answer = f"System Error: {llm_response.get('error')}"
        else:
            final_answer = llm_response.get("response", "Error generating response.")

        return {
            "answer": final_answer,
            "retrieval_metrics": retrieval_results
        }
