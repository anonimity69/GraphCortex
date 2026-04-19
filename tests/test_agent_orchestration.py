import pytest
from unittest.mock import AsyncMock, patch
from graph_cortex.core.agents.base_agent import BaseAgent

@pytest.mark.asyncio
async def test_agent_ray_serve_failure_fallback():
    """
    Ensures that if the Ray Serve LLMEngineDeployment goes down or times out,
    the agent degrades gracefully instead of crashing the REPL application.
    """
    agent = BaseAgent(name="TestAgent", system_prompt="Hello")
    
    # We mock the ray.serve.get_deployment chain to raise a Timeout/Connection Exception
    with patch('graph_cortex.core.agents.base_agent.serve') as mock_serve:
        mock_serve.get_deployment.side_effect = Exception("Ray Serve Cluster Unreachable Timeout")
        
        # Fire query
        response = await agent.query_llm(user_input="Test Query")
        
        # Verify graceful fallback format output
        assert isinstance(response, dict)
        assert response.get("status") == "error"
        assert "Ray Serve Cluster Unreachable Timeout" in response.get("error")

@pytest.mark.asyncio
async def test_agent_successful_routing():
    """
    Ensures that a successful Ray Serve RPC correctly unwraps the response payload.
    """
    agent = BaseAgent(name="TestAgent", system_prompt="Hello")
    
    with patch('graph_cortex.core.agents.base_agent.serve') as mock_serve:
        # Build the chain: serve.get_deployment().get_handle().remote()
        mock_handle = AsyncMock()
        # Mocking the async response using AsyncMock for the awaitable returned by .remote()
        mock_handle.remote.return_value = {"status": "success", "response": "Mocked LLM Result"}
        
        mock_deployment = AsyncMock()
        mock_deployment.get_handle.return_value = mock_handle
        
        mock_serve.get_deployment.return_value = mock_deployment
        
        response = await agent.query_llm(user_input="Test Query")
        
        assert response["status"] == "success"
        assert response["response"] == "Mocked LLM Result"
