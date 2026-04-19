from graph_cortex.infrastructure.db.neo4j_connection import get_session
import json

class MemoryCuration:
    """
    Dedicated logic for RL-driven memory curation (Phase 4).
    Implements a Global Soft-Delete architecture to preserve graph history.
    """
    def __init__(self):
        pass

    def merge_node(self, label: str, name: str, properties: dict = None):
        """
        Idempotently creates or updates a node during RL training.
        """
        if properties is None:
            properties = {}
        
        # Ensure we track that this was an RL-optimized node
        properties['curated_by'] = 'RL_Librarian'
        
        query = f"MERGE (n:{label} {{name: $name}}) SET n += $props RETURN n"
        with get_session() as session:
            result = session.run(query, name=name, props=properties)
            return result.single() is not None

    def update_node(self, node_id: str, properties: dict):
        """
        Updates properties of an existing node by its internal ID.
        """
        query = "MATCH (n) WHERE elementId(n) = $node_id SET n += $props RETURN n"
        with get_session() as session:
            result = session.run(query, node_id=node_id, props=properties)
            return result.single() is not None

    def set_node_active_status(self, node_id: str, status: bool = False):
        """
        Soft-deletes (or restores) a node by flagging its is_active property.
        Inactive nodes act as dead-ends for the Spreading Activation retrieval engine.
        """
        query = """
        MATCH (n) WHERE elementId(n) = $node_id
        SET n.is_active = $status
        RETURN n.name AS name, labels(n)[0] AS type, n.is_active AS is_active
        """
        with get_session() as session:
            result = session.run(query, node_id=node_id, status=status)
            record = result.single()
            if record:
                return record.data()
            return None
