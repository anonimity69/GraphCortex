import pytest
from unittest.mock import MagicMock
from graph_cortex.core.retrieval.engine import RetrievalEngine
from graph_cortex.core.agents.researcher import ResearchAgent

def test_researcher_context_formatting_with_rels():
    """
    Verifies that the Researcher agent correctly formats relationships into the context string.
    """
    agent = ResearchAgent()
    
    # Mock retrieval results
    mock_results = {
        "status": "Hit",
        "network": [
            {
                "node_id": "1",
                "name": "Alice",
                "type": "Person",
                "distance": 0,
                "path_rels": []
            },
            {
                "node_id": "2",
                "name": "Project Chimera",
                "type": "Project",
                "distance": 1,
                "path_rels": [
                    {"type": "WORKS_ON", "start_name": "Alice", "end_name": "Project Chimera"}
                ]
            },
            {
                "node_id": "3",
                "name": "Rust",
                "type": "Language",
                "distance": 2,
                "path_rels": [
                    {"type": "WORKS_ON", "start_name": "Alice", "end_name": "Project Chimera"},
                    {"type": "WRITTEN_IN", "start_name": "Project Chimera", "end_name": "Rust"}
                ]
            }
        ]
    }
    
    # We need to mock the retrieval engine's retrieve method
    agent.retrieval_engine.retrieve = MagicMock(return_value=mock_results)
    
    # We also need to mock query_llm to avoid API calls
    agent.query_llm = MagicMock(return_value={"status": "success", "response": "Mocked Answer"})
    
    import asyncio
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(agent.process_query("What does Alice write in?"))
    
    # Check the context string passed to query_llm
    # agent.query_llm.call_args[1]['context']
    context = agent.query_llm.call_args.kwargs['context']
    
    assert "### Fact Relationships (Edges):" in context
    assert "(Alice) -[WORKS_ON]-> (Project Chimera)" in context
    assert "(Project Chimera) -[WRITTEN_IN]-> (Rust)" in context
    print("Verification Success: Relationships included in context string.")

if __name__ == "__main__":
    test_researcher_context_formatting_with_rels()
