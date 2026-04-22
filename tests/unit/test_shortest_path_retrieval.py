import unittest
from unittest.mock import MagicMock
from graph_cortex.infrastructure.db.queries.retrieval_queries import get_subgraph_edges

class GetSubgraphEdgesTest(unittest.TestCase):
    def test_cypher_query_generation(self):
        """
        Verifies that get_subgraph_edges correctly formats the shortestPath query.
        """
        mock_session = MagicMock()
        node_ids = ["4:123", "4:456"]
        
        get_subgraph_edges(mock_session, node_ids)
        
        # Verify session.run was called
        self.assertTrue(mock_session.run.called)
        
        # Check the query string
        call_args = mock_session.run.call_args
        query_str = call_args.args[0]
        params = call_args.kwargs
        
        self.assertIn("shortestPath", query_str)
        self.assertIn("UNWIND", query_str)
        self.assertIn("elementId(n) IN $node_ids", query_str)
        self.assertEqual(params["node_ids"], node_ids)
        print("Success: shortestPath query generation verified.")

if __name__ == "__main__":
    unittest.main()
