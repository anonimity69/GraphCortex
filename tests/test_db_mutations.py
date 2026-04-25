import pytest
from unittest.mock import patch, MagicMock
from graph_cortex.core.memory.curation import MemoryCuration


@patch('graph_cortex.infrastructure.db.neo4j_connection.GraphDatabase.driver')
def test_soft_delete_sets_flag(mock_driver):
    mock_session = MagicMock()
    mock_driver.return_value.session.return_value.__enter__.return_value = mock_session

    mock_result = MagicMock()
    mock_result.single.return_value.data.return_value = {
        "name": "TargetNode", "type": "Entity", "is_active": False
    }
    mock_session.run.return_value = mock_result

    curation = MemoryCuration()
    result = curation.set_node_active_status("mock_id_123", False)

    assert result is not None
    assert result["is_active"] is False

    # verify the right cypher went out
    mock_session.run.assert_called_once()
    _, kwargs = mock_session.run.call_args
    assert kwargs["node_id"] == "mock_id_123"
    assert kwargs["status"] is False
