def get_anchor_nodes_by_name(session, entity_names, limit=5):
    """
    Finds anchor nodes (Entities or Concepts) matching specific string names.
    This acts as the Lexical (BM25-style) trigger in the Dual-Trigger initialization.
    """
    query = """
    UNWIND $names AS name
    MATCH (n) WHERE (n:Entity OR n:Concept) AND toLower(n.name) CONTAINS toLower(name)
    RETURN elementId(n) AS node_id, n.name AS name, labels(n)[0] AS type
    LIMIT $limit
    """
    result = session.run(query, names=entity_names, limit=limit)
    return [record.data() for record in result]


def execute_spreading_activation_hop(session, target_node_id, hop_depth):
    """
    Executes a custom Cypher BFS traversal from the target node up to a certain depth.
    Calculates raw 'degree' for downstream fan-effect attenuation.
    Note: Neo4j 5.x does not allow parameters in variable-length patterns,
    so hop_depth is safely interpolated as an integer literal.
    """
    depth = int(hop_depth)  # Sanitize to prevent injection
    query = f"""
    MATCH path = (start)-[*1..{depth}]-(connected)
    WHERE elementId(start) = $node_id
    WITH start, connected, REDUCE(s = 0, n IN nodes(path) | s + 1) AS distance,
         COUNT {{ (connected)--() }} AS degree
    RETURN 
        elementId(connected) AS node_id, 
        connected.name AS name, 
        labels(connected)[0] AS type,
        distance,
        degree
    ORDER BY distance ASC
    """
    result = session.run(query, node_id=target_node_id)
    return [record.data() for record in result]

def get_anchors_by_vector_similarity(session, vector, limit=2):
    """
    Finds anchor nodes based on semantic vector similarity (Cosine).
    Queries the 'entity_vector_index' initialized in schema_migrations.
    """
    query = """
    CALL db.index.vector.queryNodes('entity_vector_index', $limit, $vector)
    YIELD node, score
    WHERE score > 0.65  // Minimum similarity threshold to prevent hallucinated anchors
    RETURN elementId(node) AS node_id, node.name AS name, labels(node)[0] AS type, score
    ORDER BY score DESC
    """
    result = session.run(query, limit=limit, vector=vector)
    return [record.data() for record in result]
