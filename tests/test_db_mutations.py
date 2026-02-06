import pytest
from unittest.mock import patch, MagicMock
from graph_cortex.core.memory.curation import MemoryCuration

@patch('graph_cortex.infrastructure.db.neo4j_connection.GraphDatabase.driver')
def test_soft_delete_preserves_schema(mock_driver):
    """
    Tests that the soft-deletion curation logic properly formats
    the boolean flag and requests the correct Neo4j transaction without dropping nodes.
    """
    # Setup Mock
    mock_session = MagicMock()
    mock_driver.return_value.session.return_value.__enter__.return_value = mock_session
    
    mock_result = MagicMock()
    mock_result.single.return_value.data.return_value = {
        "name": "TargetNode",
        "type": "Entity",
        "is_active": False
    }
    mock_session.run.return_value = mock_result
    
    # Execute Soft Delete
    curation = MemoryCuration()
    result = curation.set_node_active_status("mock_id_123", False)
    
    # Assert
    assert result is not None
    assert result["name"] == "TargetNode"
    assert result["is_active"] is False
    
    # Verify the correct Cypher transaction was pushed to the driver
    mock_session.run.assert_called_once()
    args, kwargs = mock_session.run.call_args
    query_str = args[0]
    
    assert "SET n.is_active = $status" in query_str
    assert kwargs["node_id"] == "mock_id_123"
    assert kwargs["status"] is False
