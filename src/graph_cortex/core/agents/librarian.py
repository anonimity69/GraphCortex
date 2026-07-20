import torch
import torch.nn as nn
from torch.distributions.categorical import Categorical
import os
import logging

from graph_cortex.core.agents.base_agent import BaseAgent
from graph_cortex.core.rl.policy import LibrarianPolicy
from graph_cortex.config.embedding import encode as encode_embedding
from graph_cortex.core.memory.curation import MemoryCuration
from graph_cortex.infrastructure.db.falkordb_connection import get_graph


class LibrarianAgent(BaseAgent):
    """RL-driven graph curator. Picks ADD/UPDATE/DELETE actions via a trained policy."""

    def __init__(self, model_path: str = "librarian_policy_weights.pt"):
        super().__init__(name="Librarian", system_prompt="Autonomous Graph Curator")

        self.curation = MemoryCuration()
        self.device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")

        self.policy = LibrarianPolicy().to(self.device)

        if os.path.exists(model_path):
            try:
                self.policy.load_state_dict(torch.load(model_path, map_location=self.device))
                self.policy.eval()
                logging.info(f"Librarian loaded weights from {model_path}")
            except Exception as e:
                logging.error(f"Librarian weight load failed: {e}. Using random policy.")

        self.stats = {
            "sanitized_nodes": 0,
            "total_curations": 0,
            "actions": {"NOOP": 0, "ADD": 0, "UPDATE": 0, "DELETE": 0}
        }

    def cleanup_error_nodes(self, session_id: str) -> int:
        """Purge rate-limit and error message nodes that got stored accidentally."""
        query = """
        MATCH (m:Message)
        WHERE m.session_id = $session_id
        AND (m.content CONTAINS 'Rate limits' OR m.content CONTAINS 'System Error')
        AND (m.is_active IS NULL OR m.is_active = true)
        SET m.is_active = false
        RETURN count(m) as n
        """
        graph = get_graph()
        result = graph.query(query, params={'session_id': session_id})
        count = result.result_set[0][0] if result.result_set else 0
        if count > 0:
            self.stats["sanitized_nodes"] += count
            logging.info(f"Librarian: purged {count} error nodes from {session_id}")
        return count

    def get_stats(self) -> dict:
        return self.stats

    def _find_stale_nodes(self, session_id: str) -> list:
        """Grab low-confidence or rarely accessed nodes as deletion candidates."""
        query = """
        MATCH (n)
        WHERE n.session_id = $session_id AND n.is_active = true
          AND (n.confidence IS NOT NULL AND n.confidence < 0.3
               OR n.access_count IS NOT NULL AND n.access_count < 2)
        RETURN n.uid AS node_id, n.name AS name, labels(n)[0] AS label
        LIMIT 5
        """
        graph = get_graph()
        result = graph.query(query, params={'session_id': session_id})
        return [
            {result.header[i]: row[i] for i in range(len(result.header))}
            for row in result.result_set
        ]

    def _find_duplicate_candidates(self, session_id: str) -> list:
        """Find entity names that appear more than once in the same session."""
        query = """
        MATCH (n)
        WHERE n.session_id = $session_id AND n.is_active = true AND n.name IS NOT NULL
        WITH n.name AS name, collect(n.uid) AS ids, count(*) AS cnt
        WHERE cnt > 1
        RETURN name, ids
        LIMIT 3
        """
        graph = get_graph()
        result = graph.query(query, params={'session_id': session_id})
        return [
            {result.header[i]: row[i] for i in range(len(result.header))}
            for row in result.result_set
        ]

    def curate(self, state_text: str, session_id: str) -> dict:
        """Run one curation cycle: encode state, pick action, execute it."""
        self.cleanup_error_nodes(session_id)

        try:
            vector = encode_embedding(state_text)
            state_tensor = torch.FloatTensor(vector).to(self.device).unsqueeze(0)
        except Exception as e:
            logging.error(f"Librarian encoding failed: {e}")
            return {"status": "error", "message": "encoding_failure"}

        with torch.no_grad():
            action_probs = self.policy(state_tensor)
            m = Categorical(action_probs)
            action = m.sample().item()

        action_map = {0: "NOOP", 1: "ADD", 2: "UPDATE", 3: "DELETE"}
        action_name = action_map.get(action, "NOOP")
        info = {"action_id": action, "action_name": action_name}

        try:
            if action == 0:
                info["status"] = "noop"

            elif action == 1:
                # ADD: generate a bridging concept node from the current context
                # FIXME: ideally this should call the LLM to extract what to add
                node_name = f"curated_{session_id[:12]}_{self.stats['total_curations']}"
                self.curation.merge_node(label="Concept", name=node_name, properties={
                    "source": "librarian_rl",
                    "confidence": 0.5,
                    "session_id": session_id,
                })
                info["status"] = f"added {node_name}"

            elif action == 2:
                # UPDATE: bump confidence on stale nodes instead of deleting them
                stale = self._find_stale_nodes(session_id)
                if stale:
                    target = stale[0]
                    self.curation.update_node(
                        node_id=target["node_id"],
                        properties={"confidence": 0.6, "curated_by": "librarian"}
                    )
                    info["status"] = f"updated {target['name']}"
                else:
                    info["status"] = "nothing_to_update"

            elif action == 3:
                # DELETE: soft-delete the weakest node
                stale = self._find_stale_nodes(session_id)
                if stale:
                    target = stale[0]
                    self.curation.set_node_active_status(node_id=target["node_id"], status=False)
                    info["status"] = f"soft_deleted {target['name']}"
                else:
                    info["status"] = "nothing_to_delete"

            self.stats["total_curations"] += 1
            self.stats["actions"][action_name] += 1
            logging.info(f"Librarian: {action_name} -> {info['status']}")
            return info

        except Exception as e:
            logging.error(f"Librarian action failed: {e}")
            return {"status": "error", "message": str(e)}
