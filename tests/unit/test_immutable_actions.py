import unittest
from unittest.mock import MagicMock
from graph_cortex.core.rl.action_env import GraphMemoryEnv

class TestImmutableActions(unittest.TestCase):
    def setUp(self):
        # Mock curation to avoid real DB hits
        self.env = GraphMemoryEnv()
        self.env.curation = MagicMock()

    def test_update_immutable_property_is_blocked(self):
        """
        Verifies that attempting to update an immutable property (like 'name') 
        is blocked in the environment and logged as a violation.
        """
        action = 2  # UPDATE
        kwargs = {
            "node_id": "test_id",
            "properties": {
                "name": "Malicious Overwrite",
                "confidence": 0.95
            }
        }
        
        state, reward, done, truncated, info = self.env.step(action, kwargs)
        
        # 1. Verify 'name' was stripped but 'confidence' was passed
        passed_props = self.env.curation.update_node.call_args[1]['properties']
        self.assertNotIn("name", passed_props)
        self.assertIn("confidence", passed_props)
        self.assertEqual(passed_props["confidence"], 0.95)
        
        # 2. Verify violation was logged in 'info'
        self.assertIn("action_violation", info)
        self.assertIn("name", info["action_violation"])
        print(f"Success: Violation detected: {info['action_violation']}")

    def test_update_all_immutable_is_noop(self):
        """
        Verifies that if all properties are immutable, the database is not called at all.
        """
        action = 2 # UPDATE
        kwargs = {
            "node_id": "test_id",
            "properties": {
                "name": "Overwrite",
                "summary": "Reset"
            }
        }
        
        state, reward, done, truncated, info = self.env.step(action, kwargs)
        
        self.assertFalse(self.env.curation.update_node.called)
        self.assertEqual(info["status"], "skipping_empty_safe_update")
        self.assertIn("action_violation", info)
        print("Success: Purely destructive update was completely blocked.")

if __name__ == "__main__":
    unittest.main()
