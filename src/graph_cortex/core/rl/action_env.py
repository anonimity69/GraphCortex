"""
Gymnasium-compatible Environment for the Librarian Agents.
Bridges discrete LLM policy actions (ADD, UPDATE, SOFT-DELETE, NOOP) 
to actual neo4j database transactions.
"""

import gymnasium as gym
from gymnasium import spaces
from typing import Dict, Any

from graph_cortex.infrastructure.db.neo4j_connection import get_session
from graph_cortex.core.memory.curation import MemoryCuration

class GraphMemoryEnv(gym.Env):
    """
    Simulated Environment where a Librarian Agent observes a local neighborhood
    of the Knowledge Graph and decides which curation action to take.
    """
    def __init__(self, config: Dict[str, Any] = None):
        super(GraphMemoryEnv, self).__init__()
        self.curation = MemoryCuration()
        self.current_state = None
        
        # Actions: 0 (NOOP), 1 (ADD), 2 (UPDATE), 3 (SOFT-DELETE)
        # We define a discrete action space for conventional RL, but 
        # LLMs will generate string tokens that we map to these ints.
        self.action_space = spaces.Discrete(4)
        
        # Textual observation space (Prompt structure)
        self.observation_space = spaces.Text(max_length=10000)

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        # In a real training loop, 'reset' loads a new training question and 
        # retrieves the initial starting subgraph.
        initial_context = options.get('subgraph_context', "Empty Graph") if options else "Empty Graph"
        self.current_state = initial_context
        return self.current_state, {}

    def step(self, action: int, action_kwargs: dict):
        """
        Executes a curation action on the graph.
        action_kwargs requires 'node_id', 'target_id' etc. depending on action.
        """
        reward = 0.0 # Delayed reward is injected externally via LLM Judge
        done = True  # We do Single-Step episodes for now
        info = {"action_taken": action}
        
        try:
            if action == 0:  # NOOP
                info["status"] = "skipping"
            elif action == 1:  # ADD
                pass # Trigger neo4j MERGE logic (Implemented in next iteration)
            elif action == 2:  # UPDATE
                pass # Trigger neo4j property SET logic
            elif action == 3:  # SOFT-DELETE
                node_id = action_kwargs.get("node_id")
                if node_id:
                    self.curation.set_node_active_status(node_id=node_id, status=False)
                    info["status"] = f"soft_deleted_{node_id}"
                else:
                    info["status"] = "error_missing_node_id"
        except Exception as e:
            info["status"] = f"error: {str(e)}"
            
        # Return observation, reward, terminated, truncated, info
        return self.current_state, reward, done, False, info
