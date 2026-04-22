from graph_cortex.core.agents.base_agent import BaseAgent
import logging
from graph_cortex.core.retrieval.engine import RetrievalEngine
from graph_cortex.config.llm import DEFAULT_RESEARCHER_PROMPT

class ResearchAgent(BaseAgent):
    """
    The Research Agent is responsible for querying the memory graph
    and formatting the retrieved context for the user answering phase.
    """
    def __init__(self):
        super().__init__(name="Researcher", system_prompt=DEFAULT_RESEARCHER_PROMPT)
        self.retrieval_engine = RetrievalEngine()
        
    async def process_query(self, user_query: str, session_id: str) -> dict:
        """
        1. Retrieve memory context (Lexical + Semantic)
        2. Format Context
        3. Query LLM to formulate an answer
        """
        logging.info(f"[{self.name}] Retrieving context for query: '{user_query}' in session '{session_id}'")
        
        # We pass the full query string as a single-element list to the engine
        retrieval_results = self.retrieval_engine.retrieve([user_query], session_id=session_id)
        
        context_string = ""
        if retrieval_results["status"] == "Hit":
            nodes = retrieval_results["network"]
            context_string = "Retrieved Knowledge Graph Context:\n"
            
            # First, list unique nodes
            context_string += "### Entities & Concepts:\n"
            for node in nodes:
                context_string += f"- ({node['type']}) {node['name']} [Distance: {node['distance']}]\n"
            
            # Second, list connecting relationships (Reconstructed Sub-graph)
            context_string += "\n### Fact Relationships (Edges):\n"
            edges = retrieval_results.get("edges", [])
            for edge in edges:
                rel_str = f"({edge['source_name']}) -[{edge['rel_type']}]-> ({edge['target_name']})"
                context_string += f"- {rel_str}\n"
                
            logging.info(f"[{self.name}] Found {len(nodes)} nodes and {len(edges)} edges.")
        else:
            logging.info(f"[{self.name}] No relevant context found. Proceeding with zero-shot.")
            
        # Send to deployed LLM Engine
        logging.info(f"[{self.name}] Awaiting LLM response...")
        llm_response = await self.query_llm(user_input=user_query, context=context_string)
        
        if llm_response.get("status") == "error":
            final_answer = f"System Error: {llm_response.get('error')}"
        else:
            final_answer = llm_response.get("response", "Error generating response.")
            
        return {
            "answer": final_answer,
            "retrieval_metrics": retrieval_results
        }
