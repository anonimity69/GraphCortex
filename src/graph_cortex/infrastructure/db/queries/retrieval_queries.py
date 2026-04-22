from graph_cortex.config.retrieval import SEMANTIC_SIMILARITY_THRESHOLD, LEXICAL_ANCHOR_LIMIT, SEMANTIC_ANCHOR_LIMIT

def get_anchors_by_fulltext(session, search_string, session_id, limit=LEXICAL_ANCHOR_LIMIT):
    """
    Finds anchor nodes (Entities or Concepts) using a Fulltext BM25 index search.
    This replaces the exact substring match with probabilistic keyword relevance.
    """
    query = """
    CALL db.index.fulltext.queryNodes("hybrid_entity_concept", $search_string)
    YIELD node, score
    WHERE coalesce(node.is_active, true) = true AND node.session_id = $session_id
    RETURN elementId(node) AS node_id, node.name AS name, labels(node)[0] AS type, score
    ORDER BY score DESC
    LIMIT $limit
    """
    result = session.run(query, search_string=search_string, session_id=session_id, limit=limit)
    return [record.data() for record in result]


def execute_spreading_activation_hop(session, target_node_id, session_id, hop_depth):
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
      AND connected.session_id = $session_id
      AND coalesce(connected.is_active, true) = true
      AND ALL(node IN nodes(path) WHERE node.session_id = $session_id AND coalesce(node.is_active, true) = true)
    WITH start, connected, length(path) AS distance,
         relationships(path) AS rels,
         COUNT {{ (connected)--() }} AS degree
    RETURN 
        elementId(connected) AS node_id, 
        connected.name AS name, 
        labels(connected)[0] AS type,
        distance,
        degree,
        [r in rels | {{type: type(r), start_name: startNode(r).name, end_name: endNode(r).name}}] AS path_rels
    ORDER BY distance ASC
    """
    result = session.run(query, node_id=target_node_id, session_id=session_id)
    return [record.data() for record in result]

def get_anchors_by_vector_similarity(session, vector, session_id, limit=SEMANTIC_ANCHOR_LIMIT):
    """
    Finds anchor nodes based on semantic vector similarity (Cosine).
    Queries the 'entity_vector_index' initialized in schema_migrations.
    """
    query = """
    CALL db.index.vector.queryNodes('entity_vector_index', $limit, $vector)
    YIELD node, score
    WHERE score > $threshold
      AND coalesce(node.is_active, true) = true
      AND node.session_id = $session_id
    RETURN elementId(node) AS node_id, node.name AS name, labels(node)[0] AS type, score
    ORDER BY score DESC
    """
    result = session.run(query, limit=limit, vector=vector, session_id=session_id, threshold=SEMANTIC_SIMILARITY_THRESHOLD)
    return [record.data() for record in result]
def get_subgraph_edges(session, node_ids, session_id):
    """
    Explicitly reconstructs the connections between a cluster of activated nodes.
    Uses shortestPath to ensure connecting 'middle' nodes are captured even if 
    their individual activation energy was below the threshold.
    """
    if not node_ids:
        return []
        
    query = """
    MATCH (n), (m)
    WHERE elementId(n) IN $node_ids 
      AND elementId(m) IN $node_ids 
      AND n.session_id = $session_id
      AND m.session_id = $session_id
      AND elementId(n) < elementId(m)
    MATCH p = shortestPath((n)-[*1..3]-(m))
    UNWIND relationships(p) AS r
    WITH DISTINCT r
    RETURN 
        elementId(startNode(r)) AS source_id, 
        startNode(r).name AS source_name, 
        type(r) AS rel_type, 
        elementId(endNode(r)) AS target_id, 
        endNode(r).name AS target_name
    """
    result = session.run(query, node_ids=node_ids, session_id=session_id)
    return [record.data() for record in result]
