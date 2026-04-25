import pytest
from unittest.mock import AsyncMock, patch
from graph_cortex.core.agents.base_agent import BaseAgent


@pytest.mark.anyio
async def test_llm_failure_returns_error():
    agent = BaseAgent(name="TestAgent", system_prompt="Hello")

    with patch('graph_cortex.core.agents.base_agent.LLMClient.query', new_callable=AsyncMock) as mock:
        mock.return_value = {"status": "error", "error": "API Key Invalid or Expired"}
        response = await agent.query_llm(user_input="Test Query")

        assert response["status"] == "error"
        assert "API Key Invalid" in response["error"]


@pytest.mark.anyio
async def test_successful_query():
    agent = BaseAgent(name="TestAgent", system_prompt="Hello")

    with patch('graph_cortex.core.agents.base_agent.LLMClient.query', new_callable=AsyncMock) as mock:
        mock.return_value = {"status": "success", "response": "Mocked LLM Result"}
        response = await agent.query_llm(user_input="Test Query")

        assert response["status"] == "success"
        assert response["response"] == "Mocked LLM Result"
