from graph_cortex.config.retrieval import SEMANTIC_SIMILARITY_THRESHOLD, LEXICAL_ANCHOR_LIMIT, SEMANTIC_ANCHOR_LIMIT


def get_anchors_by_fulltext(graph, search_string, session_id, limit=LEXICAL_ANCHOR_LIMIT):
    """Fulltext search on :Searchable super-label via FalkorDB's RediSearch index."""
    query = """
    CALL db.idx.fulltext.queryNodes('Searchable', $search_string)
    YIELD node, score
    WHERE node.is_active = true AND node.session_id = $session_id
    RETURN node.uid AS node_id, node.name AS name, labels(node)[0] AS type, score
    ORDER BY score DESC
    LIMIT $limit
    """
    result = graph.query(query, params={
        'search_string': search_string,
        'session_id': session_id,
        'limit': limit
    })
    return [
        {result.header[i]: row[i] for i in range(len(result.header))}
        for row in result.result_set
    ]


def get_anchors_by_vector_similarity(graph, vector, session_id, limit=SEMANTIC_ANCHOR_LIMIT):
    """Vector similarity search across Entity and Concept nodes via UNION."""
    # FalkorDB requires separate vector queries per label, combined with UNION
    # We query each label independently and merge in Python for cleaner control
    results = []

    for label in ['Entity', 'Concept']:
        query = f"""
        CALL db.idx.vector.queryNodes('{label}', 'embedding', $limit, vecf32($vector))
        YIELD node, score
        WHERE node.session_id = $session_id AND node.is_active = true AND score > $threshold
        RETURN node.uid AS node_id, node.name AS name, '{label}' AS type, score
        ORDER BY score DESC
        LIMIT $limit
        """
        result = graph.query(query, params={
            'limit': limit,
            'vector': vector,
            'session_id': session_id,
            'threshold': SEMANTIC_SIMILARITY_THRESHOLD
        })
        for row in result.result_set:
            results.append({result.header[i]: row[i] for i in range(len(result.header))})

    # sort merged results by score descending and limit
    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:limit]


def get_neighbors(graph, node_uid, session_id):
    """Get immediate neighbors of a node for A* traversal."""
    query = """
    MATCH (start {uid: $node_uid})-[r]-(neighbor)
    WHERE neighbor.session_id = $session_id
      AND neighbor.is_active = true
    RETURN neighbor.uid AS node_id,
           neighbor.name AS name,
           labels(neighbor)[0] AS type,
           type(r) AS rel_type,
           neighbor.embedding AS embedding
    """
    result = graph.query(query, params={
        'node_uid': node_uid,
        'session_id': session_id
    })
    return [
        {result.header[i]: row[i] for i in range(len(result.header))}
        for row in result.result_set
    ]


def execute_spreading_activation_hop(graph, target_node_uid, session_id, hop_depth):
    """Multi-hop spreading activation from a single anchor node."""
    depth = int(hop_depth)
    query = f"""
    MATCH path = (start)-[*1..{depth}]-(connected)
    WHERE start.uid = $node_uid
      AND connected.session_id = $session_id
      AND connected.is_active = true
      AND ALL(node IN nodes(path) WHERE node.session_id = $session_id AND node.is_active = true)
    WITH start, connected, length(path) AS distance,
         relationships(path) AS rels
    RETURN
        connected.uid AS node_id,
        connected.name AS name,
        labels(connected)[0] AS type,
        distance,
        SIZE([(connected)--() | 1]) AS degree,
        [r in rels | {{type: type(r), start_name: startNode(r).name, end_name: endNode(r).name}}] AS path_rels
    ORDER BY distance ASC
    """
    result = graph.query(query, params={
        'node_uid': target_node_uid,
        'session_id': session_id
    })
    return [
        {result.header[i]: row[i] for i in range(len(result.header))}
        for row in result.result_set
    ]


def get_subgraph_edges(graph, node_uids, session_id):
    """Reconstruct edges between activated nodes. Uses shortestPath to bridge gaps."""
    if not node_uids:
        return []

    query = """
    MATCH (n), (m)
    WHERE n.uid IN $node_uids
      AND m.uid IN $node_uids
      AND n.session_id = $session_id
      AND m.session_id = $session_id
      AND n.uid < m.uid
    MATCH p = shortestPath((n)-[*1..3]-(m))
    UNWIND relationships(p) AS r
    WITH DISTINCT r
    RETURN
        startNode(r).uid AS source_id,
        startNode(r).name AS source_name,
        type(r) AS rel_type,
        endNode(r).uid AS target_id,
        endNode(r).name AS target_name
    """
    result = graph.query(query, params={
        'node_uids': node_uids,
        'session_id': session_id
    })
    return [
        {result.header[i]: row[i] for i in range(len(result.header))}
        for row in result.result_set
    ]
