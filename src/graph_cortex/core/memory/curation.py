from graph_cortex.infrastructure.db.neo4j_connection import get_session


class MemoryCuration:
    """Graph mutation ops used by the Librarian agent. All deletes are soft."""

    def merge_node(self, label: str, name: str, properties: dict = None):
        if properties is None:
            properties = {}
        properties['curated_by'] = 'RL_Librarian'

        query = f"MERGE (n:{label} {{name: $name}}) SET n += $props RETURN n"
        with get_session() as session:
            result = session.run(query, name=name, props=properties)
            return result.single() is not None

    def update_node(self, node_id: str, properties: dict):
        query = "MATCH (n) WHERE elementId(n) = $node_id SET n += $props RETURN n"
        with get_session() as session:
            result = session.run(query, node_id=node_id, props=properties)
            return result.single() is not None

    def set_node_active_status(self, node_id: str, status: bool = False):
        """Soft-delete or restore. Bridges FOLLOWS chain around deactivated event nodes."""
        query = """
        MATCH (n) WHERE elementId(n) = $node_id
        SET n.is_active = $status
        
        WITH n
        WHERE $status = false
        
        OPTIONAL MATCH (prev)-[r1:FOLLOWS]->(n)
        OPTIONAL MATCH (n)-[r2:FOLLOWS]->(next)
        
        FOREACH (_ IN CASE WHEN prev IS NOT NULL AND next IS NOT NULL THEN [1] ELSE [] END |
            MERGE (prev)-[:FOLLOWS]->(next)
        )
        
        RETURN n.name AS name, labels(n)[0] AS type, n.is_active AS is_active
        """
        with get_session() as session:
            result = session.run(query, node_id=node_id, status=status)
            record = result.single()
            if record:
                return record.data()
            return None
