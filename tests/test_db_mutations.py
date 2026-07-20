import pytest
from unittest.mock import patch, MagicMock
from graph_cortex.core.memory.curation import MemoryCuration


@patch('graph_cortex.infrastructure.db.falkordb_connection.FalkorDB')
def test_soft_delete_sets_flag(mock_falkordb):
    mock_graph = MagicMock()
    mock_falkordb.return_value.select_graph.return_value = mock_graph

    mock_result = MagicMock()
    mock_result.result_set = [["TargetNode", "Entity", False]]
    mock_result.header = ["name", "type", "is_active"]
    mock_graph.query.return_value = mock_result

    curation = MemoryCuration()
    # Patch the get_graph to return our mock
    with patch('graph_cortex.core.memory.curation.get_graph', return_value=mock_graph):
        result = curation.set_node_active_status("mock_uid_123", False)

    assert result is not None
    assert result["is_active"] is False

    # verify the right cypher went out
    mock_graph.query.assert_called_once()
    _, kwargs = mock_graph.query.call_args
    assert kwargs["params"]["node_id"] == "mock_uid_123"
    assert kwargs["params"]["status"] is False
