import pytest
from unittest.mock import AsyncMock, patch
from graph_cortex.core.agents.base_agent import BaseAgent

@pytest.mark.anyio
async def test_agent_llm_failure_fallback():
    """
    Ensures that if the direct LLM Client fails (e.g., API error),
    the agent handles it gracefully.
    """
    agent = BaseAgent(name="TestAgent", system_prompt="Hello")
    
    # We patch the LLMClient's query method to return an error status
    with patch('graph_cortex.core.agents.base_agent.LLMClient.query', new_callable=AsyncMock) as mock_query:
        mock_query.return_value = {"status": "error", "error": "API Key Invalid or Expired"}
        
        # Fire query
        response = await agent.query_llm(user_input="Test Query")
        
        # Verify graceful fallback format output
        assert isinstance(response, dict)
        assert response.get("status") == "error"
        assert "API Key Invalid" in response.get("error")

@pytest.mark.anyio
async def test_agent_successful_query():
    """
    Ensures that a successful LLM query correctly returns the response.
    """
    agent = BaseAgent(name="TestAgent", system_prompt="Hello")
    
    with patch('graph_cortex.core.agents.base_agent.LLMClient.query', new_callable=AsyncMock) as mock_query:
        mock_query.return_value = {"status": "success", "response": "Mocked LLM Result"}
        
        response = await agent.query_llm(user_input="Test Query")
        
        assert response["status"] == "success"
        assert response["response"] == "Mocked LLM Result"
