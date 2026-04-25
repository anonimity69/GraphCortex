import gymnasium as gym
from gymnasium import spaces
from typing import Dict, Any

from graph_cortex.infrastructure.db.neo4j_connection import get_session
from graph_cortex.core.memory.curation import MemoryCuration

# properties the librarian is never allowed to touch
IMMUTABLE_PROPS = {"name", "summary", "content", "purpose", "event_id", "message_id"}


class GraphMemoryEnv(gym.Env):
    """Gym env bridging discrete RL actions to neo4j curation ops."""

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__()
        self.curation = MemoryCuration()
        self.current_state = None
        self.action_space = spaces.Discrete(4)  # NOOP, ADD, UPDATE, SOFT-DELETE
        self.observation_space = spaces.Text(max_length=10000)

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        initial_context = options.get('subgraph_context', "Empty Graph") if options else "Empty Graph"
        self.current_state = initial_context
        return self.current_state, {}

    def step(self, action: int, action_kwargs: dict):
        reward = 0.0  # injected externally by the LLM judge
        done = True
        info = {"action_taken": action}

        try:
            if action == 0:
                info["status"] = "skipping"
            elif action == 1:
                name = action_kwargs.get("name", "NewNode")
                label = action_kwargs.get("label", "Entity")
                self.curation.merge_node(label=label, name=name, properties=action_kwargs.get("properties", {}))
                info["status"] = f"added_{label}_{name}"
            elif action == 2:
                node_id = action_kwargs.get("node_id")
                raw_props = action_kwargs.get("properties", {})

                # enforce immutability
                filtered = {k: v for k, v in raw_props.items() if k not in IMMUTABLE_PROPS}
                violated = [k for k in raw_props if k in IMMUTABLE_PROPS]

                if violated:
                    info["action_violation"] = f"blocked immutable keys: {violated}"

                if node_id and filtered:
                    self.curation.update_node(node_id=node_id, properties=filtered)
                    info["status"] = f"updated_{node_id}"
                elif node_id:
                    info["status"] = "noop_empty_update"
                else:
                    info["status"] = "error_missing_node_id"
            elif action == 3:
                node_id = action_kwargs.get("node_id")
                if node_id:
                    self.curation.set_node_active_status(node_id=node_id, status=False)
                    info["status"] = f"soft_deleted_{node_id}"
                else:
                    info["status"] = "error_missing_node_id"
        except Exception as e:
            info["status"] = f"error: {e}"

        return self.current_state, reward, done, False, info
