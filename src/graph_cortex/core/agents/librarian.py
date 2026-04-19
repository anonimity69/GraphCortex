import torch
import torch.nn as nn
from torch.distributions.categorical import Categorical
import os
import logging

from graph_cortex.core.agents.base_agent import BaseAgent
from graph_cortex.core.rl.policy import LibrarianPolicy
from graph_cortex.config.embedding import encode as encode_embedding
from graph_cortex.core.memory.curation import MemoryCuration
from graph_cortex.infrastructure.db.neo4j_connection import get_session

class LibrarianAgent(BaseAgent):
    """
    The Librarian Agent is responsible for autonomous graph curation.
    It uses a trained PyTorch policy to ADD, UPDATE, or SOFT-DELETE nodes
    to optimize the retrieval performance of the memory swarm.
    """
    def __init__(self, model_path: str = "librarian_policy_weights.pt"):
        # The Librarian doesn't strictly need a system prompt for its RL logic,
        # but we inherit from BaseAgent to maintain consistency in the swarm.
        super().__init__(name="Librarian", system_prompt="Autonomous Graph Curator")
        
        self.curation = MemoryCuration()
        self.device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
        
        # Load the Policy 
        self.policy = LibrarianPolicy().to(self.device)
        
        if os.path.exists(model_path):
            try:
                self.policy.load_state_dict(torch.load(model_path, map_location=self.device))
                self.policy.eval()
                logging.info(f"[{self.name}] Successfully loaded trained weights from {model_path}")
            except Exception as e:
                logging.error(f"[{self.name}] Failed to load model weights: {e}. Falling back to random policy.")
        else:
            logging.warning(f"[{self.name}] Weights file '{model_path}' not found. Operating with random initialization.")

    def cleanup_error_nodes(self) -> int:
        """
        Hard-coded heuristic to purge 'Rate limit' or 'System Error' messages from the graph.
        Returns the count of soft-deleted nodes.
        """
        query = """
        MATCH (m:Message)
        WHERE (m.content CONTAINS 'Rate limits' OR m.content CONTAINS 'System Error')
        AND (m.is_active IS NULL OR m.is_active = true)
        SET m.is_active = false
        RETURN count(m) as deleted_count
        """
        with get_session() as session:
            result = session.run(query)
            record = result.single()
            count = record["deleted_count"] if record else 0
            if count > 0:
                logging.info(f"[{self.name}] Sanitized {count} error-related nodes from the memory graph.")
            return count

    def curate(self, state_text: str) -> dict:
        """
        Observes the current textual state, performs inference, and executes a mutation.
        """
        # 0. Auto-Sanitize Phase
        self.cleanup_error_nodes()
        
        # 1. State Encoding
        try:
            vector = encode_embedding(state_text)
            state_tensor = torch.FloatTensor(vector).to(self.device).unsqueeze(0)
        except Exception as e:
            logging.error(f"[{self.name}] State encoding failed: {e}")
            return {"status": "error", "message": "encoding_failure"}

        # 2. Policy Inference
        with torch.no_grad():
            action_probs = self.policy(state_tensor)
            m = Categorical(action_probs)
            action = m.sample().item()

        # 3. Action Execution
        info = {"action_id": action}
        
        # We need a heuristic for action_kwargs in production if not explicitly provided.
        # For now, we use a basic mapping based on the action type.
        try:
            if action == 0:  # NOOP
                info["status"] = "skipping"
            elif action == 1:  # ADD
                # In production, we might want to prompt an LLM to generate the node data,
                # but for the RL loop integration, we act on the current context.
                info["status"] = "add_pending_llm_generation" 
            elif action == 2:  # UPDATE
                info["status"] = "update_pending_target_id"
            elif action == 3:  # SOFT-DELETE
                info["status"] = "delete_pending_target_id"
                
            logging.info(f"[{self.name}] Decision: Action {action} ({info['status']})")
            return info
            
        except Exception as e:
            logging.error(f"[{self.name}] Execution failed: {e}")
            return {"status": "error", "message": str(e)}
