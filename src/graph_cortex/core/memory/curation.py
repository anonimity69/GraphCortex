from graph_cortex.infrastructure.db.falkordb_connection import get_graph


class MemoryCuration:
    """Graph mutation ops used by the Librarian agent. All deletes are soft."""

    def merge_node(self, label: str, name: str, properties: dict = None):
        if properties is None:
            properties = {}
        properties['curated_by'] = 'RL_Librarian'

        query = f"MERGE (n:{label} {{name: $name}}) SET n += $props RETURN n.uid AS uid"
        graph = get_graph()
        result = graph.query(query, params={'name': name, 'props': properties})
        return len(result.result_set) > 0

    def update_node(self, node_id: str, properties: dict):
        query = "MATCH (n) WHERE n.uid = $node_id SET n += $props RETURN n.uid AS uid"
        graph = get_graph()
        result = graph.query(query, params={'node_id': node_id, 'props': properties})
        return len(result.result_set) > 0

    def set_node_active_status(self, node_id: str, status: bool = False):
        """Soft-delete or restore. Bridges FOLLOWS chain around deactivated event nodes."""
        query = """
        MATCH (n) WHERE n.uid = $node_id
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
        graph = get_graph()
        result = graph.query(query, params={'node_id': node_id, 'status': status})
        if result.result_set:
            header = result.header
            row = result.result_set[0]
            return {header[i]: row[i] for i in range(len(header))}
        return None
